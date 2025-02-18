import { DialogueRole, cancelSession, isChildCardConfirmValidSelector } from "@aacesstalk/libs/ts-core";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { PopupMenuItemView } from "apps/client-rn/src/components/PopupMenuItemView";
import { PopupMenuScreenFrame } from "apps/client-rn/src/components/PopupMenuScreenFrame";
import { MainRoutes } from "apps/client-rn/src/navigation";
import { useDispatch, useSelector } from "apps/client-rn/src/redux/hooks";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Alert } from "react-native";
import { useMoveNextTurn } from "../hooks";

export const SessionMenuPopupScreen = (props: NativeStackScreenProps<MainRoutes.MainNavigatorParamList, "session-menu">) => {
    
    const {t} = useTranslation()

    const sessionId = useSelector(state => state.session.id)
    const numTurns = useSelector(state => state.session.numTurns)
    const currentTurn = useSelector(state => state.session.currentTurn)

    const canSubmitSelectedChildCards = useSelector(isChildCardConfirmValidSelector)

    const pop = useCallback(()=>{
        props.navigation.goBack()
    },[])

    const dispatch = useDispatch()

    const onTerminationPress = useCallback(()=>{

        if(numTurns <= 1){
            console.log("The user did nothing. Just terminate the session without asking.")
            dispatch(cancelSession())
            requestAnimationFrame(props.navigation.popToTop)
        }else{
            Alert.alert(t("Session.Menu.ConfirmTermination"), null, [
                {text: t("Session.Menu.CancelTermination"), style: 'cancel'},
                {text: t("Session.Menu.TerminateAndSave"), style: 'default', onPress: () => {
                    props.navigation.replace(MainRoutes.ROUTE_SESSION_CLOSING, { sessionId, numStars: Math.floor(numTurns/2) })
                }},
            ], {cancelable: true})
        }
    }, [t, numTurns, sessionId])

    const onNextTurnPress = useMoveNextTurn(useCallback((turn: DialogueRole)=>{
        props.navigation.pop()
        }, [props.navigation]))
    
    return <PopupMenuScreenFrame onPop={pop}>
        <PopupMenuItemView title={t("Session.Menu.NextTurn")} onPress={onNextTurnPress} disabled={!((currentTurn == DialogueRole.Child && canSubmitSelectedChildCards) || currentTurn == DialogueRole.Parent)}/>
        <PopupMenuItemView title={t("Session.Menu.TerminateSession")} destructive onPress={onTerminationPress}/>
    </PopupMenuScreenFrame>
}