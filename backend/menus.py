"""기본 메뉴 목록(L11, PRD R14). 앱이 제공하는 고정 목록이며 사용자 데이터가 아니라 DB에 저장하지 않는다.

각 메뉴는 음식 종류 하나에 속한다(예: 짜장면 → CHINESE). id는 목록 순서대로 1부터 붙인다.
"""

from backend.schemas import Menu

_MENU_NAMES = {
    "KOREAN": ["김치찌개", "된장찌개", "비빔밥", "제육볶음", "국밥", "불고기", "순두부찌개", "냉면", "칼국수", "삼계탕"],
    "CHINESE": ["짜장면", "짬뽕", "탕수육", "마라탕", "볶음밥", "마파두부", "깐풍기", "울면", "양장피", "마라샹궈"],
    "JAPANESE": ["초밥", "돈까스", "라멘", "우동", "규동", "가츠동", "소바", "오야코동", "카레라이스", "텐동"],
    "WESTERN": ["파스타", "피자", "햄버거", "스테이크", "리조또", "샐러드", "샌드위치", "오믈렛", "그라탱", "필라프"],
    "SNACK": ["떡볶이", "김밥", "라볶이", "순대", "튀김", "쫄면", "라면", "어묵", "주먹밥", "만두"],
    "ETC": ["쌀국수", "팟타이", "커리", "타코", "부리또", "케밥", "반미", "분짜", "나시고렝", "포케"],
}

MENUS: list[Menu] = [
    Menu(id=index, name=name, category=category)
    for index, (category, name) in enumerate(
        ((category, name) for category, names in _MENU_NAMES.items() for name in names), start=1
    )
]
