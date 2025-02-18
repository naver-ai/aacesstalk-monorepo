import { SessionTopicInfo } from "@aacesstalk/libs/ts-core"

export namespace MainRoutes{
    export const ROUTE_HOME = "home"
    export const ROUTE_STAR_LIST = "stars"
    export const ROUTE_FREE_TOPIC_SELECTION = "free-topic-selection"
    export const ROUTE_SESSION = "session"
    export const ROUTE_SESSION_CLOSING = "session-closing"
    export const ROUTE_SESSION_MENU = "session-menu"

    export type MainNavigatorParamList = {
        [ROUTE_HOME]: undefined,
        [ROUTE_STAR_LIST]: undefined,
        [ROUTE_FREE_TOPIC_SELECTION]: undefined,
        [ROUTE_SESSION]: {topic: SessionTopicInfo},
        [ROUTE_SESSION_MENU]: undefined,
        [ROUTE_SESSION_CLOSING]: {sessionId: string, numStars: number}
    }
}