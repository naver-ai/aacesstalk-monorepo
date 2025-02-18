import { DialogueRole, TopicCategory, startAndRetrieveInitialParentGuide } from '@aacesstalk/libs/ts-core'
import { NativeStackScreenProps } from '@react-navigation/native-stack'
import { MainRoutes } from 'apps/client-rn/src/navigation'
import HillPlanImage from '../../../assets/images/hill_plan.svg'
import HillRecallImage from '../../../assets/images/hill_recall.svg'
import HillFreeImage from '../../../assets/images/hill_free.svg'
import { HillBackgroundView } from 'apps/client-rn/src/components/HillBackgroundView'
import { useTranslation } from 'react-i18next'
import { useDispatch, useSelector } from 'apps/client-rn/src/redux/hooks'
import { Fragment, useCallback, useEffect, useMemo } from 'react'
import { SessionParentView } from '../components/parent/SessionParentView'
import { TailwindButton } from 'apps/client-rn/src/components/tailwind-components'
import { MenuIcon } from 'apps/client-rn/src/components/vector-icons'
import Animated, { Easing, SlideInDown } from 'react-native-reanimated'
import { LoadingIndicator } from 'apps/client-rn/src/components/LoadingIndicator'
import { SessionChildView } from '../components/child/SessionChildView'
import { TailwindClasses } from 'apps/client-rn/src/styles'
import { useDisableBack, usePrevious } from 'apps/client-rn/src/utils/hooks'
import { startRecording, stopRecording } from '../../audio/reducer'
import { InteractionManager, View } from 'react-native'
import { useEnterKeyEvent, useMoveNextTurn } from '../hooks'
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context'
import { twMerge } from 'tailwind-merge'

const BG_COLOR_BY_TOPIC_CATEGORY = {
    [TopicCategory.Plan]: 'bg-topicplan-bg',
    [TopicCategory.Recall]: 'bg-topicrecall-bg',
    [TopicCategory.Free]: 'bg-topicfree-bg',
}

export const SessionScreen = (props: NativeStackScreenProps<MainRoutes.MainNavigatorParamList, "session">) => {

    const { t } = useTranslation()

    useDisableBack()

    const dispatch = useDispatch()

    const isInitializing = useSelector(state => state.session.isInitializing)
    const isLoadingRecommendation = useSelector(state => state.session.isProcessingRecommendation)
    const sessionId = useSelector(state => state.session.id)

    const currentTurn = useSelector(state => state.session.currentTurn)
    const pTurn = usePrevious(currentTurn)

    const turnId = useSelector(state => state.session.currentTurnId)

    useEffect(()=>{
        if(pTurn != currentTurn && sessionId != null && turnId != null && currentTurn == DialogueRole.Parent){
            console.log("ParentTurn started.")
            InteractionManager.runAfterInteractions(()=>{
                dispatch(startRecording())
            })
        }

        return () => {
            if(pTurn != currentTurn && sessionId != null && turnId != null && currentTurn == DialogueRole.Parent){
                console.log("Parent turn finished.")
            }
        }
    }, [pTurn, currentTurn, sessionId, turnId])

    useEffect(() => {
        if (isInitializing == false && sessionId != null) {
            dispatch(startAndRetrieveInitialParentGuide())
        }
    }, [isInitializing, sessionId])

    useEffect(()=>{
        return () => {
            dispatch(stopRecording(true))
        }
    }, [])

    const onNextTurnPress = useMoveNextTurn()

    useEnterKeyEvent(true, useCallback(()=>{
        onNextTurnPress()
        return true
    }, [onNextTurnPress]))

    let HillView
    switch (props.route.params.topic.category) {
        case TopicCategory.Plan:
            HillView = HillPlanImage
            break;
        case TopicCategory.Recall:
            HillView = HillRecallImage
            break;
        case TopicCategory.Free:
            HillView = HillFreeImage
            break;
        default:
            throw Error("Unsupported topic category.")
    }

    const onMenuButtonPress = useCallback(() => {
        props.navigation.navigate('session-menu')
    }, [])

    const insets = useSafeAreaInsets()


    const menuButtonClassName = useMemo(()=>{
        return twMerge("absolute left-5", insets.bottom == 0 ? "bottom-5" : "bottom-2")
    }, [insets.bottom])

    return <HillBackgroundView containerClassName={`items-center ${BG_COLOR_BY_TOPIC_CATEGORY[props.route.params.topic.category]}`} 
        hillComponentClass={HillView} hillImageHeight={165}>

        <SafeAreaView className="flex-1 self-stretch items-center justify-center" mode='margin'>
        {
            isInitializing === true ? <LoadingIndicator colorTopic={props.route.params.topic.category} label={t("Session.LoadingMessage.Initializing")} useImage={true} containerClassName='absolute justify-center self-center left-0 right-0 top-0 bottom-0'/> : null
        }
        <Fragment key={"session-content"}>
            {
                currentTurn === DialogueRole.Parent ? <SessionParentView topic={props.route.params.topic}/> : <SessionChildView/>
            }
        </Fragment>
        
        {
            (!isInitializing && !isLoadingRecommendation) ?
            <View className={menuButtonClassName}>
                <TailwindButton className={menuButtonClassName} onPress={onMenuButtonPress} roundedClassName='rounded-xl' buttonStyleClassName={`p-3 ${TailwindClasses.ICON_BUTTON_SIZES}`}><MenuIcon width={32} height={32} fill={"#575757"} /></TailwindButton>
            </View> : null
        } 
        </SafeAreaView>
    </HillBackgroundView>
}