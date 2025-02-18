import { ParentGuideType, parentGuideMessageSelector, parentGuideSelectors, requestParentGuideExampleMessage } from "@aacesstalk/libs/ts-core";
import { LoadingIndicator } from "apps/client-rn/src/components/LoadingIndicator";
import { useDispatch, useSelector } from "apps/client-rn/src/redux/hooks"
import { getTopicColorClassNames, styleTemplates } from "apps/client-rn/src/styles"
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import FeedbackLegImage from '../../../../assets/images/feedback-leg.svg'
import { Pressable, Text, View, StyleSheet } from "react-native"
import Animated ,{ Easing, ZoomIn, interpolate, interpolateColor, useAnimatedStyle, useSharedValue, withSpring, withTiming } from 'react-native-reanimated';

const styles = StyleSheet.create({
    guideFrame: {
        shadowColor: "rgba(0,0,0)",
        shadowOpacity: 0.3,
        shadowOffset: {width: 0, height: 10},
        shadowRadius: 10,
        elevation: 10,
        //boxShadow: "0 15 15 rgba(0,0,50,0.1)"
    },

    feedbackLegLeft: {
        position: 'absolute', top: -15, left: 20
    },

    feedbackLegRight: {
        position: 'absolute', top: -15, right: 20
    }
})

interface Props{id: string, order: number}

const TEXT_MESSAGE_CLASSNAME = "text-2xl text-white text-center"

const GUIDE_FRAME_DIMENSION_CLASSNAME = "w-[70vw] h-[16vh]"

const GUIDE_FRAME_CLASSNAME = `absolute ${GUIDE_FRAME_DIMENSION_CLASSNAME} justify-center px-8 rounded-2xl border-white border-[6px]`

export const ParentGuideElementView = (props: Props) => {
    const guideType = useSelector(state => parentGuideSelectors.selectById(state, props.id)?.type)

    switch(guideType){
        case ParentGuideType.Messaging:
            return <ParentMessageGuideElementView id={props.id} order={props.order} />
        case ParentGuideType.Feedback:
            return <ParentFeedbackElementView id={props.id} order={props.order}/>
    }
}

const ParentMessageGuideElementView = (props: Props) => {
    const dispatch = useDispatch()

    const topicCategory = useSelector(state => state.session.topic.category)
    const guideMessage = useSelector(state => parentGuideMessageSelector(state, props.id))
    const isExampleLoading = useSelector(state => state.session.parentExampleMessageLoadingFlags[props.id] || false)
    const exampleMessage = useSelector(state => state.session.parentExampleMessages[props.id])

    const [isExampleMessageShown, setIsExampleMessageShown] = useState(false)

    const enteringAnim = useMemo(() => ZoomIn.springify().duration(600).delay(props.order * 100), [props.order])

    const pressAnimProgress = useSharedValue(0)

    const {t} = useTranslation()

    const exampleTransitionAnimProgress = useSharedValue(0)

    const exampleLoadingModeAnimProgress = useSharedValue(0)

    const onPressIn = useCallback(()=>{
        pressAnimProgress.value = withTiming(1, {duration: 200, easing: Easing.out(Easing.cubic)})
    }, [])

    const onPressOut = useCallback(()=>{
        pressAnimProgress.value = withSpring(0, {duration: 500})
    }, [])

    const runFlipAnim = useCallback((flipTo: 0|1)=>{
        exampleTransitionAnimProgress.value = withTiming(flipTo, {duration: 800, easing: Easing.elastic(1)})
    }, [])

    const onPress = useCallback(()=>{
            if(!isExampleMessageShown && !isExampleLoading){
                if(exampleMessage == null){
                        exampleLoadingModeAnimProgress.value = withTiming(1, {duration: 400, easing: Easing.out(Easing.cubic)})
                        dispatch(requestParentGuideExampleMessage(props.id, () => {
                            runFlipAnim(1)
                            exampleLoadingModeAnimProgress.value = withTiming(0, {duration: 400, easing: Easing.in(Easing.cubic)})
                        }))
                    
                }else{
                    runFlipAnim(1)
                }
                setIsExampleMessageShown(true)
            }else{
                setIsExampleMessageShown(false)
                runFlipAnim(0)
            }
    }, [props.id, isExampleMessageShown, exampleMessage, isExampleLoading, setIsExampleMessageShown])

    const containerAnimStyle = useAnimatedStyle(() => {
        return {
            transform: [
                {scale: interpolate(pressAnimProgress.value, [0, 1], [1, 0.90])},
                {translateY: interpolate(pressAnimProgress.value, [0, 1], [0, 5])},
        ] as any
        }
    }, [isExampleMessageShown])

    const guideMessageAnimStyle = useAnimatedStyle(()=>{
        return {
            shadowColor: interpolateColor(exampleTransitionAnimProgress.value,[0, 0.2], ["rgba(0,0,50,0.3)", "rgba(0,0,50,0)"], "RGB"),
            transform: [
                {rotateY: `${interpolate(exampleTransitionAnimProgress.value,[0, 1], [0, 180])}deg`}
            ],
            opacity: exampleTransitionAnimProgress.value > 0.5 ? 0 : 1,
        }
    }, [])

    const exampleMessageAnimStyle = useAnimatedStyle(()=>{
        return {
            opacity: exampleTransitionAnimProgress.value > 0.5 ? 1 : 0,
            shadowColor: interpolateColor(exampleTransitionAnimProgress.value,[0.8, 1], ["rgba(0,0,50,0)", "rgba(0,0,50,0.3)"], "RGB"),
            transform: [
                {rotateY: `${interpolate(exampleTransitionAnimProgress.value,[0, 1], [180, 360])}deg`}
            ]
        }
    }, [])

    const guideMessageTextAnimStyle = useAnimatedStyle(()=>{
        return {
            opacity: interpolate(exampleLoadingModeAnimProgress.value, [0,1], [1,0], 'clamp'),
        }
    }, [])

    const exampleMessageLoadingIndicatorAnimStyle = useAnimatedStyle(()=>{
        return {
            opacity: interpolate(exampleLoadingModeAnimProgress.value, [0,1], [0,1], 'clamp'),
        }
    }, [])

    const [guideMessageFrameBackgroundClassName, exampleMessageFrameBackgroundClassName] = useMemo(()=>{
        return getTopicColorClassNames(topicCategory)
    }, [topicCategory])
    
    return <Animated.View entering={enteringAnim}>
            <Pressable accessible={false} onPress={onPress} onPressIn={onPressIn} onPressOut={onPressOut} >
                <Animated.View style={containerAnimStyle} className={`${GUIDE_FRAME_DIMENSION_CLASSNAME}`}>
                    <Animated.View style={[styles.guideFrame, guideMessageAnimStyle]} className={`${GUIDE_FRAME_CLASSNAME} ${guideMessageFrameBackgroundClassName}`}>
                        <Animated.Text style={[styleTemplates.withSemiboldFont, guideMessageTextAnimStyle]} className={`${TEXT_MESSAGE_CLASSNAME}`}>{guideMessage}</Animated.Text>
                        <Animated.View className="absolute self-center" style={exampleMessageLoadingIndicatorAnimStyle}><LoadingIndicator color="white" titleClassName="text-white" label={t("Session.LoadingMessage.ParentExample")} horizontal/></Animated.View>
                    </Animated.View>
                    <Animated.View style={[styles.guideFrame, exampleMessageAnimStyle]} className={`${GUIDE_FRAME_CLASSNAME} ${exampleMessageFrameBackgroundClassName}`}>
                        <Text style={styleTemplates.withHandwritingFont} className={`${TEXT_MESSAGE_CLASSNAME} !text-black text-3xl`}>"{exampleMessage?.message_localized || exampleMessage?.message}"</Text>
                    </Animated.View>
                </Animated.View>
            </Pressable>
        </Animated.View>
}

const ParentFeedbackElementView = (props: Props) => {


    const guideMessage = useSelector(state => state.session.parentGuideEntityState.entities[props.id].guide_localized || state.session.parentGuideEntityState.entities[props.id].guide)
    
    return <View>
        <FeedbackLegImage style={styles.feedbackLegLeft}/> 
        <FeedbackLegImage style={styles.feedbackLegRight}/>   
        <View className={`bg-[#f2d359] rounded-2xl border-[#daba3e] border-2 border-b-[7px] justify-center ${GUIDE_FRAME_DIMENSION_CLASSNAME} shadow-lg shadow-black`}>
            <Text style={styleTemplates.withSemiboldFont} className={`${TEXT_MESSAGE_CLASSNAME} !text-black px-6`}>{guideMessage}</Text>
        </View>    
    </View>
}