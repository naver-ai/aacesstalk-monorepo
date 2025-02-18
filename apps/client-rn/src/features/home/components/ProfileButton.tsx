import { signOutDyadThunk } from "@aacesstalk/libs/ts-core"
import { useDispatch, useSelector } from "apps/client-rn/src/redux/hooks"
import { styleTemplates } from "apps/client-rn/src/styles"
import { useCallback, useMemo } from "react"
import { useTranslation } from "react-i18next"
import { Alert, View, Text } from "react-native"
import { Gesture, GestureDetector } from "react-native-gesture-handler"
import format from 'pupa'

export const ProfileButton = (props: {
    containerClassName?: string
}) => {
    const child_name = useSelector(state => state.auth.dyadInfo?.child_name)
    const parent_type = useSelector(state => state.auth.dyadInfo?.parent_type)

    const [t] = useTranslation()

    const dispatch = useDispatch()

    const label = useMemo(()=>{
        return format(t("DyadInfo.FamilyLabelTemplate"), {child_name: child_name || "", parent_type: t(`DyadInfo.ParentType.${parent_type}`)})
    }, [t, child_name, parent_type, t])

    const onTripplePress = useCallback(()=>{
        Alert.alert(t("SignIn.ConfirmSignOut"), null, [{text: t("SignIn.Cancel"), style: 'cancel'}, {text: t("SignIn.SignOut"), onPress: () => {
            dispatch(signOutDyadThunk())
        }, style: 'destructive'}], {cancelable: true})
    }, [t, dispatch])

    const tripleTap = useMemo(()=>Gesture.Tap().runOnJS(true).maxDuration(600).numberOfTaps(3)
    .onStart(onTripplePress), [onTripplePress])
    
    return <GestureDetector gesture={tripleTap}><View className={props.containerClassName}>
            <Text className={`text-lg text-center text-slate-400`} style={styleTemplates.withSemiboldFont}>{label}</Text>
        </View></GestureDetector>
}