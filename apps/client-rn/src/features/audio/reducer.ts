import { PayloadAction, createSlice } from "@reduxjs/toolkit";
import { AudioEncoderAndroidType, AudioSet, AudioSourceAndroidType, OutputFormatAndroidType } from 'react-native-audio-recorder-player'
import { Lazy } from "../../utils/lazy";
import AudioRecorderPlayer, { RecordBackType } from "react-native-audio-recorder-player";
import { ClientThunk } from "../../redux/store";
import { Dirs, FileSystem } from "react-native-file-access";
import { CoreThunk, Http, makeSubmitParentMessageThunk } from "@aacesstalk/libs/ts-core";
import {AxiosError} from 'axios'
import ReactNativeBlobUtil from 'react-native-blob-util';


export enum RecordingStatus{
    Initial="initial",
    Preparing="preparing",
    Recording="recording",
    RecordingPause="recording-pause",
    Stopping="stopping"
}

export interface ParentAudioRecordingState{
    status: RecordingStatus
    recordingStartedTimestamp?: number,
    recordingDurationMillis: number,
    recordingMeter?: number
}

const INITIAL_STATE: ParentAudioRecordingState = {
    status: RecordingStatus.Initial,
    recordingMeter: undefined,
    recordingDurationMillis: 0,
    recordingStartedTimestamp: undefined
}

const parentAudioRecordingSlice = createSlice({
    name: 'parentAudioRecording',
    initialState: INITIAL_STATE,
    reducers: {
        setRecordingStatus:(state, action: PayloadAction<RecordingStatus>) => {
            state.status = action.payload
            if(action.payload == RecordingStatus.Stopping || action.payload == RecordingStatus.Initial){
                state.recordingMeter = undefined
            }
        },
        setRecordingStartTimestamp: (state, action: PayloadAction<number|undefined>) => {
            state.recordingStartedTimestamp = action.payload
        }, 

        setRecordingArgs: (state, action: PayloadAction<RecordBackType>) => {
            state.recordingMeter = action.payload.currentMetering
            state.recordingDurationMillis = action.payload.currentPosition
        }
    }
})

export default parentAudioRecordingSlice.reducer


const DEFAULT_AUDIO_SETTINGS: AudioSet = {
    AudioEncoderAndroid: AudioEncoderAndroidType.AAC,
    AudioSourceAndroid: AudioSourceAndroidType.MIC,
    OutputFormatAndroid: OutputFormatAndroidType.MPEG_4,
}

const recorder = new Lazy(() => {
    const player = new AudioRecorderPlayer()
    player.setSubscriptionDuration(0.1)
    return player
} )
let isRecordingActive = false

export function startRecording(recordingStartedTimestamp: number = Date.now()): ClientThunk {
    return async (dispatch, getState) => {
        const state = getState()
        const sessionId = state.session.id
        const turnId = state.session.currentTurnId
        console.log("session id: ", sessionId)
        console.log("turn id: ", turnId)
        const audioDirPath = Dirs.CacheDir + "/audio_recording"
        if(await FileSystem.exists(audioDirPath) == false){
            await FileSystem.mkdir(audioDirPath)
        }
        const audioFilePath = audioDirPath + `/${sessionId}_${turnId}_${Date.now()}.m4a`

        if(isRecordingActive == false && state.parentAudioRecording.status == RecordingStatus.Initial){
            console.log("Recording started.")
            isRecordingActive = true
            dispatch(parentAudioRecordingSlice.actions.setRecordingStatus(RecordingStatus.Preparing))
            recorder.get().addRecordBackListener((args) => {
                dispatch(parentAudioRecordingSlice.actions.setRecordingArgs(args))
            })
            await recorder.get().startRecorder( audioFilePath , DEFAULT_AUDIO_SETTINGS, true)
            dispatch(parentAudioRecordingSlice.actions.setRecordingStartTimestamp(recordingStartedTimestamp))
            dispatch(parentAudioRecordingSlice.actions.setRecordingStatus(RecordingStatus.Recording))
        }
    }
}

export function pauseRecording(): ClientThunk {
    return async (dispatch, getState) => {
        const state = getState()
        if(isRecordingActive == true && state.parentAudioRecording.status == RecordingStatus.Recording){
            await recorder.get().pauseRecorder()
            dispatch(parentAudioRecordingSlice.actions.setRecordingStatus(RecordingStatus.RecordingPause))
        }
    }
}

export function resumeRecording(){
    return async (dispatch, getState) => {
        const state = getState()
        if(isRecordingActive == true && state.parentAudioRecording.status == RecordingStatus.RecordingPause){
            await recorder.get().resumeRecorder()
            dispatch(parentAudioRecordingSlice.actions.setRecordingStatus(RecordingStatus.Recording))
        }
    }
}

export function stopRecording(cancel: boolean = false): ClientThunk{
    return async (dispatch, getState, extraArgument) => {
        const state = getState()
        if(isRecordingActive == true && (state.parentAudioRecording.status == RecordingStatus.RecordingPause || state.parentAudioRecording.status == RecordingStatus.Recording)){
            console.log("Recording stopped.")
            isRecordingActive = false
            dispatch(parentAudioRecordingSlice.actions.setRecordingStatus(RecordingStatus.Stopping))
            const uri = await recorder.get().stopRecorder()
            recorder.get().removeRecordBackListener()
            recorder.delete()
            console.log("audio file recorded at: ", uri)
            if(cancel){
                console.log("recording was canceled. remove audio file")
                if(await FileSystem.exists(uri)){
                    await FileSystem.unlink(uri)
                }
            }
            dispatch(parentAudioRecordingSlice.actions.setRecordingStatus(RecordingStatus.Initial))

            if(!cancel){
                submitParentMessageFromAudio(uri)(dispatch, getState, extraArgument)
            }
        }
    }
}

export function submitParentMessageFromAudio(uri: string): CoreThunk {
    return makeSubmitParentMessageThunk(async (dispatch, getState) => {
            const state = getState()
        
            console.log("Try uploading...", uri)

            //Convert file into binary string
            //const binary = Buffer.from(b64, 'base64').toString('binary')

            const pathSplit = uri.split("/")
            const fileName = pathSplit[pathSplit.length - 1]

            try{
                const headers = {
                    ...(await Http.getSignedInHeaders(state.auth.jwt)),
                    'Content-Type': 'multipart/form-data'
                }

                const response = await ReactNativeBlobUtil.fetch('POST', Http.axios.defaults.baseURL + Http.ENDPOINT_DYAD_MEDIA_RECOGNIZE_SPEECH,
                    headers,
                    [
                        {name: 'session_id', data: state.session.id},
                        {name: 'turn_id', data: state.session.currentTurnId},
                        {name: 'file', filename: fileName, type: 'audio/m4a', data: ReactNativeBlobUtil.wrap(uri)}
                    ])

                if(response.info().status == 200){
                    const dictatedText: string = response.data
                    console.log("Dictated text: ", dictatedText)
                    return dictatedText
                }else{
                    throw response.data
                }

            }catch(ex){
                console.log(ex)
                return null
            }
    })
}