from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user
from app.core.database import get_db
from app.models.board import Post
from app.models.user import User

# ─── 샘플 데이터 (네이버 API 키 없이 테스트용, 6줄 요약) ───
_SEED_HEALTH = [
    {"title": "고혈압 예방을 위한 생활습관 개선 7가지", "summary": "고혈압은 전 세계 심뇌혈관 질환의 가장 주요한 위험인자로, 국내 성인 3명 중 1명이 고혈압 환자입니다.\n하루 30분 이상의 유산소 운동은 수축기 혈압을 평균 4~9mmHg 낮출 수 있어 혈압 관리에 매우 효과적입니다.\n나트륨 섭취를 하루 2,000mg 이하로 줄이는 저염식은 혈압을 약 2~8mmHg 낮추는 것으로 연구에서 확인됐습니다.\n금연은 혈관 탄성을 회복시키고, 금주는 혈압 상승의 직접적 원인을 제거하는 데 도움을 줍니다.\n과체중 감량은 체중 1kg 감소당 혈압을 약 1mmHg 낮추는 효과가 있어 체중 관리가 중요합니다.\n규칙적인 수면과 스트레스 관리도 혈압 변동성을 줄이는 데 필수적인 요소입니다.", "tags": ["고혈압", "혈압관리", "심혈관", "생활습관"]},
    {"title": "수면 부족이 건강에 미치는 위험 신호", "summary": "성인 기준 하루 7~9시간의 수면이 권장되며, 6시간 미만의 수면은 만성 질환의 위험을 크게 높입니다.\n수면 부족은 식욕 조절 호르몬인 렙틴을 감소시키고 그렐린을 증가시켜 과식과 비만으로 이어질 수 있습니다.\n만성 수면 부족은 혈당 조절 능력을 저하시켜 제2형 당뇨병 발병 위험을 최대 2배까지 높입니다.\n수면 중 분비되는 멜라토닌은 면역 기능 강화에 관여하므로, 수면 부족 시 감염에 취약해질 수 있습니다.\n깊은 수면 단계에서 뇌의 노폐물이 청소되며, 이 과정이 방해받으면 인지 기능과 기억력이 저하됩니다.\n수면의 질을 높이려면 취침 전 1시간은 블루라이트를 피하고, 규칙적인 취침 시간을 유지하는 것이 중요합니다.", "tags": ["수면", "건강", "피로", "수면부족"]},
    {"title": "당뇨병 예방을 위한 올바른 식단 구성법", "summary": "제2형 당뇨병은 생활습관 개선만으로 발병 위험을 58% 이상 줄일 수 있다는 연구 결과가 있습니다.\n정제 탄수화물(흰쌀, 흰 빵, 설탕)은 혈당을 급격히 올리므로 통곡물과 잡곡으로 대체하는 것이 좋습니다.\n식이섬유가 풍부한 채소를 매 식사의 절반 이상 차지하도록 하면 혈당 상승 속도를 효과적으로 늦출 수 있습니다.\n하루 세 끼 규칙적인 식사는 인슐린 분비를 안정화시키고, 과식을 예방하는 데 도움이 됩니다.\n단백질(두부, 닭가슴살, 생선) 섭취는 포만감을 높이고 근육량 유지에 기여해 혈당 관리에 유리합니다.\n식후 가벼운 10~15분 산책만으로도 식후 혈당 스파이크를 크게 완화할 수 있습니다.", "tags": ["당뇨", "혈당관리", "식단", "예방"]},
    {"title": "면역력 강화를 위한 필수 영양소 가이드", "summary": "면역 체계는 다양한 영양소가 균형 있게 공급될 때 최적으로 기능하므로 편식은 면역력 저하의 주요 원인입니다.\n비타민C는 면역 세포의 기능을 강화하며, 파프리카·키위·브로콜리에 풍부하게 함유되어 있습니다.\n비타민D는 면역 조절에 핵심적인 역할을 하며, 하루 20분 야외 활동으로 피부에서 합성될 수 있습니다.\n아연은 면역 세포 생성에 필수적이며, 굴·소고기·호박씨 등에 풍부하게 들어 있습니다.\n오메가3 지방산은 염증 반응을 조절하여 만성 염증으로 인한 면역력 저하를 예방하는 데 도움을 줍니다.\n프로바이오틱스(유산균) 섭취는 장내 면역 기능을 강화하여 전반적인 면역력 향상에 기여합니다.", "tags": ["면역력", "영양소", "비타민", "건강관리"]},
    {"title": "심혈관 건강을 지키는 7가지 생활 습관", "summary": "심혈관 질환은 전 세계 사망 원인 1위이지만, 생활습관 개선으로 80%까지 예방이 가능합니다.\n주 5회 이상 30분의 유산소 운동은 심박출량을 늘리고 혈관 탄성을 유지시켜 심장 건강에 필수적입니다.\n지중해식 식단(올리브오일, 생선, 채소 중심)은 심혈관 질환 발병 위험을 30% 이상 낮추는 것으로 입증됐습니다.\n흡연은 혈관 내피를 손상시키고 동맥경화를 가속화하므로 금연이 심혈관 건강에 가장 중요한 단일 요소입니다.\n만성 스트레스는 코르티솔 수치를 높여 혈압 상승과 부정맥을 유발할 수 있어 관리가 필요합니다.\n혈압·콜레스테롤·혈당은 40세 이상부터 연 1회 이상 정기 검진을 통해 조기에 발견하고 관리해야 합니다.", "tags": ["심혈관", "심장건강", "예방", "생활습관"]},
    {"title": "비만 예방을 위한 대사 관리 방법", "summary": "비만은 단순히 외형의 문제가 아니라 고혈압, 당뇨, 관절 질환, 수면 무호흡증 등 다양한 합병증의 원인입니다.\n기초대사율을 높이기 위해 근력운동으로 근육량을 늘리면 하루 종일 칼로리 소모량이 자연스럽게 증가합니다.\n단백질은 소화 과정에서 탄수화물보다 더 많은 에너지를 소모하고 포만감을 지속시켜 과식을 예방합니다.\n하루 7~9시간 충분한 수면은 식욕 조절 호르몬 균형을 유지시켜 체중 관리에 간접적으로 기여합니다.\n하루 2L 이상의 충분한 수분 섭취는 신진대사를 원활하게 하고 공복감과 배고픔을 구분하는 데 도움을 줍니다.\n급격한 다이어트보다는 주 0.5~1kg 감량 속도를 목표로 한 지속 가능한 식단과 운동 조합이 효과적입니다.", "tags": ["비만", "대사", "체중관리", "다이어트"]},
    {"title": "정신건강 관리가 신체 건강에 미치는 영향", "summary": "정신건강과 신체건강은 밀접하게 연결되어 있으며, 만성 스트레스는 신체 여러 기관에 직접적인 영향을 줍니다.\n스트레스 호르몬인 코르티솔이 지속적으로 높으면 면역력이 저하되고 혈압 상승, 혈당 조절 이상이 발생합니다.\n우울증과 불안 장애는 수면 장애와 식욕 변화를 통해 체중과 심혈관 건강에도 영향을 미칩니다.\n하루 30분 유산소 운동은 세로토닌과 엔도르핀을 분비시켜 항우울제에 필적하는 기분 개선 효과를 줍니다.\n마음 챙김 명상을 주 3회 이상 꾸준히 실천하면 편도체의 과활성화를 억제해 스트레스 반응이 줄어듭니다.\n가족, 친구 등 사회적 지지망을 유지하는 것이 심리적 안정과 면역 기능 유지에 중요하다는 연구 결과가 있습니다.", "tags": ["정신건강", "스트레스", "명상", "웰빙"]},
    {"title": "장 건강을 위한 프로바이오틱스 완전 가이드", "summary": "인체의 장내에는 약 100조 개의 미생물이 살고 있으며, 이 미생물 생태계의 균형이 전반적인 건강을 좌우합니다.\n프로바이오틱스(유산균)는 장내 유익균을 늘려 소화 기능을 향상시키고 유해균의 증식을 억제합니다.\n김치, 된장, 청국장, 요거트, 케피어 등 발효식품은 자연 상태의 프로바이오틱스 공급원으로 매일 섭취를 권장합니다.\n식이섬유(프리바이오틱스)는 유익균의 먹이가 되므로, 채소·과일·통곡물과 함께 섭취하면 효과가 배가됩니다.\n장내 미생물은 세로토닌 생성에 관여해 기분과 정신건강에도 영향을 미치며, 이를 '장-뇌 축'이라고 합니다.\n항생제 복용 후에는 유익균도 함께 사라지므로 복용 중과 이후 2~4주간 프로바이오틱스 섭취를 늘리는 것이 좋습니다.", "tags": ["장건강", "프로바이오틱스", "발효식품", "면역"]},
    {"title": "항산화 음식으로 노화를 늦추는 방법", "summary": "노화는 활성산소(자유라디칼)가 세포를 손상시키는 과정에서 가속화되며, 항산화 물질이 이를 중화합니다.\n블루베리는 안토시아닌 함량이 높아 뇌 기능 보호와 피부 노화 억제에 효과적인 대표적 항산화 식품입니다.\n녹차에 함유된 EGCG(에피갈로카테킨 갈레이트)는 세포 노화를 억제하고 암 예방 가능성도 연구되고 있습니다.\n토마토의 리코펜은 심혈관 질환과 전립선암 예방에 효과적이며, 가열 조리 시 흡수율이 더 높아집니다.\n견과류(호두, 아몬드)의 비타민E는 세포막을 산화 손상으로부터 보호하는 지용성 항산화제 역할을 합니다.\n다양한 색깔의 채소와 과일을 하루 400g 이상 섭취하는 것이 WHO가 권장하는 항산화 영양 기준입니다.", "tags": ["항산화", "노화방지", "건강식품", "영양"]},
    {"title": "만성 스트레스를 줄이는 호흡법과 명상", "summary": "만성 스트레스는 교감신경을 지속적으로 자극해 심박수와 혈압을 높이고 면역 기능을 약화시킵니다.\n복식 호흡은 횡격막을 자극해 부교감신경을 활성화시키며, 하루 10분 실천으로 스트레스 반응이 완화됩니다.\n4-7-8 호흡법(4초 들이쉬기, 7초 참기, 8초 내쉬기)은 즉각적인 긴장 완화 효과가 있어 위기 상황에서 유용합니다.\n마음 챙김(mindfulness) 명상은 과거나 미래에 대한 걱정에서 현재 순간으로 주의를 되돌려 불안을 줄여줍니다.\n하버드 의대 연구에 따르면, 8주간의 명상 프로그램이 뇌의 편도체 크기를 줄여 스트레스 반응을 구조적으로 변화시킵니다.\n취침 전 5~10분의 이완 명상은 수면의 질을 높이고 다음 날의 인지 기능과 감정 조절 능력을 향상시킵니다.", "tags": ["스트레스관리", "호흡법", "명상", "마음챙김"]},
]

_SEED_EXERCISE = [
    {"title": "플랭크 운동 올바른 자세와 초보자 가이드", "summary": "플랭크는 복부, 허리, 엉덩이 등 코어 근육 전체를 동시에 강화하는 가장 효율적인 맨몸 운동 중 하나입니다.\n올바른 자세는 팔꿈치를 어깨 아래에 두고, 몸통을 발끝부터 머리까지 일직선으로 유지하는 것이 핵심입니다.\n엉덩이가 너무 올라가거나 허리가 처지면 척추에 무리가 가므로 거울을 보며 자세를 확인하는 것이 좋습니다.\n초보자는 20~30초부터 시작해 매주 5~10초씩 늘려 최종적으로 1~2분 유지를 목표로 합니다.\n플랭크를 꾸준히 하면 자세 교정, 요통 예방, 운동 중 부상 방지 효과를 동시에 얻을 수 있습니다.\n기본 플랭크가 익숙해지면 사이드 플랭크, 리버스 플랭크로 변형해 다양한 근육군을 자극할 수 있습니다.", "tags": ["플랭크", "코어운동", "근력운동", "자세"]},
    {"title": "초보자를 위한 홈트레이닝 4주 루틴", "summary": "홈트레이닝은 헬스장 등록 비용 없이 언제 어디서나 할 수 있어 운동 습관을 처음 시작하기에 최적입니다.\n1~2주차는 스쿼트, 푸시업, 런지 각 3세트 10회를 목표로 하여 기초 근력과 운동 습관을 형성합니다.\n3~4주차에는 버피테스트, 마운틴 클라이머를 추가해 심폐 기능과 전신 근력을 함께 향상시킵니다.\n세트 사이 휴식 시간은 30~60초를 유지하며, 운동 전 5분 동적 스트레칭은 부상 예방에 필수입니다.\n주 3~4회 규칙적인 실천이 근육 성장과 체지방 감소 효과를 최대화하며, 주 1~2회 완전 휴식도 중요합니다.\n4주 후에는 동작당 반복 횟수를 늘리거나 운동 시간을 연장하는 방식으로 점진적 과부하를 적용하세요.", "tags": ["홈트레이닝", "맨몸운동", "초보자", "루틴"]},
    {"title": "유산소 운동이 심폐 기능에 미치는 효과", "summary": "유산소 운동은 심장을 강화하고 폐 용량을 늘려 산소 운반 능력을 높이는 가장 효과적인 방법입니다.\nWHO는 성인에게 주 150분 이상의 중강도 유산소 운동을 권장하며, 이는 심혈관 질환 위험을 35% 낮춥니다.\n달리기는 가장 접근하기 쉬운 유산소 운동으로, 초보자는 3분 걷기·2분 달리기 인터벌로 시작하는 것이 좋습니다.\n자전거는 관절 충격이 적어 무릎과 발목에 부담 없이 심폐 기능을 향상시킬 수 있는 좋은 대안입니다.\n수영은 전신 근육을 사용하는 동시에 물의 저항으로 근력도 함께 키울 수 있는 복합 유산소 운동입니다.\n꾸준히 유산소 운동을 하면 안정 시 심박수가 낮아지고 최대 산소 섭취량(VO2max)이 향상됩니다.", "tags": ["유산소운동", "심폐기능", "달리기", "건강"]},
    {"title": "운동 전후 스트레칭이 중요한 이유", "summary": "스트레칭은 운동 효과를 극대화하고 부상을 예방하는 필수 과정으로, 많은 운동인들이 간과하는 습관입니다.\n운동 전 동적 스트레칭(관절 돌리기, 레그 스윙 등)은 혈류를 증가시키고 근육을 활성화해 부상 위험을 낮춥니다.\n반대로 운동 전 정적 스트레칭(30초 이상 고정)은 근력을 일시적으로 감소시키므로 운동 후에 실시하는 것이 좋습니다.\n운동 후 정적 스트레칭은 수축된 근육을 이완시키고 유산소 제거를 촉진해 근육통과 회복 시간을 줄여줍니다.\n각 근육군을 15~30초씩 천천히 늘리며 통증이 없는 범위에서 실시하고, 호흡을 멈추지 않는 것이 원칙입니다.\n폼롤러를 이용한 마이오파시아 이완(근막 이완)은 스트레칭 효과를 더욱 높이고 운동 후 회복을 가속화합니다.", "tags": ["스트레칭", "부상예방", "유연성", "운동"]},
    {"title": "근력운동이 기초대사율을 높이는 원리", "summary": "기초대사율이란 아무것도 하지 않을 때 신체가 소비하는 에너지로, 근육량이 많을수록 높아집니다.\n근육 조직은 지방 조직보다 단위 무게당 약 3배 더 많은 칼로리를 소비해 체중 관리에 유리합니다.\n근력운동 후 24~48시간 동안 근육 재합성과 회복을 위한 추가 칼로리 소모(EPOC)가 지속됩니다.\n스쿼트, 데드리프트, 벤치프레스 등 복합 동작은 여러 근육군을 동시에 자극해 시간 효율이 높습니다.\n근육 성장을 위해서는 체중 1kg당 1.6~2.2g의 단백질 섭취와 충분한 수면이 반드시 병행되어야 합니다.\n주 2~3회, 각 45~60분의 근력운동을 꾸준히 하면 6개월 내에 기초대사율이 눈에 띄게 향상됩니다.", "tags": ["근력운동", "기초대사율", "근육", "체중관리"]},
    {"title": "척추 측만증 예방을 위한 자세 교정 운동", "summary": "현대인의 장시간 좌식 생활은 척추 주변 근육의 불균형을 초래해 측만증과 만성 요통의 주요 원인이 됩니다.\n바른 자세의 기본은 귀-어깨-엉덩이-발목이 일직선이 되도록 유지하는 것이며, 이를 의식적으로 습관화해야 합니다.\n고양이-소 자세(Cat-Cow Stretch)는 척추 전체의 유연성을 높이고 주변 근육을 균형 있게 자극하는 효과적인 운동입니다.\n플랭크와 버드독 운동으로 코어 근육을 강화하면 척추를 안정시키는 자연스러운 지지대 역할을 합니다.\n모니터는 눈높이에, 의자는 무릎이 90도가 되도록 조정하고 1시간마다 5분 스트레칭 휴식을 취하세요.\n증상이 심한 경우 물리치료사의 맞춤형 운동 처방을 받는 것이 자가 운동보다 안전하고 효과적입니다.", "tags": ["자세교정", "척추", "척추측만증", "코어"]},
    {"title": "매일 만보 걷기의 실제 건강 효과", "summary": "하루 만보(약 8km) 걷기는 심혈관 건강, 혈당 조절, 체중 관리, 정신건강에 두루 효과가 있는 가장 쉬운 운동입니다.\n미국 하버드 의대 연구에서 하루 7,500보 이상 걷는 사람은 심혈관 질환 위험이 60% 낮다는 결과가 나왔습니다.\n식후 15분 이상의 걷기는 혈당 스파이크를 낮추는 데 매우 효과적이며, 특히 당뇨 예방과 관리에 유익합니다.\n걷기는 뼈와 관절에 적절한 자극을 주어 골밀도를 유지하고 관절 연골의 영양 공급을 돕습니다.\n만보를 한 번에 채우기보다 출퇴근 시 한 정류장 걷기, 점심시간 산책처럼 일상에 분산시키는 것이 실천하기 쉽습니다.\n빠른 걷기(분당 100보 이상)는 일반 걷기보다 칼로리 소모가 높고 심폐 기능 향상 효과도 크게 높아집니다.", "tags": ["걷기운동", "만보", "유산소", "생활운동"]},
    {"title": "수영이 관절 건강에 특히 좋은 이유", "summary": "수영은 물의 부력이 체중의 90%를 지지해 줘 관절에 가해지는 충격을 최소화하는 저충격 전신 운동입니다.\n관절염, 척추 질환, 비만 환자처럼 다른 운동이 어려운 분들에게 재활 운동으로 가장 많이 권장됩니다.\n자유형, 배영, 평영 등 영법마다 주로 사용하는 근육군이 달라 다양하게 병행하면 전신 균형 발달에 유리합니다.\n수중에서 움직이는 것만으로도 물의 저항이 근력 강화 효과를 주어 별도 웨이트 없이도 근육을 단련할 수 있습니다.\n수영은 심폐 기능 향상에도 탁월해 주 3회, 45분 이상 꾸준히 하면 폐 용량이 눈에 띄게 증가합니다.\n클로린(염소)에 의한 피부 자극이 우려된다면 수영 후 충분한 샤워와 보습을 통해 피부를 관리해 주세요.", "tags": ["수영", "관절건강", "저충격운동", "재활"]},
    {"title": "요가로 유연성과 스트레스를 동시에 잡는 법", "summary": "요가는 자세, 호흡, 명상을 결합한 신체-정신 통합 수련법으로 수천 년의 역사를 가진 건강 관리 방법입니다.\n꾸준한 요가 수련은 근육의 유연성과 관절 가동 범위를 늘려 일상적인 동작을 더욱 편안하게 만듭니다.\n코어 근육과 안정화 근육을 강화하는 자세들이 많아 요통 예방과 자세 교정에도 효과적입니다.\n요가의 호흡법(pranayama)은 부교감신경을 활성화시켜 스트레스 호르몬 수준을 낮추는 데 도움을 줍니다.\n연구에 따르면 주 2~3회 요가 수련이 8주 후 우울 증상과 불안 수준을 유의미하게 낮추는 것으로 나타났습니다.\n초보자는 하타 요가나 음 요가처럼 느린 속도의 입문 스타일로 시작해 몸에 무리 없이 적응하는 것이 좋습니다.", "tags": ["요가", "유연성", "스트레스해소", "명상"]},
    {"title": "HIIT 고강도 인터벌 트레이닝 완벽 가이드", "summary": "HIIT는 고강도 운동과 짧은 휴식을 반복하는 방식으로, 20~30분 안에 일반 운동 1시간의 효과를 낼 수 있습니다.\n운동 후 12~24시간 동안 대사율이 높게 유지되는 '후연소 효과(EPOC)'가 체지방 감소에 특히 효과적입니다.\n타바타(20초 전력 운동-10초 휴식 × 8세트)가 가장 유명한 HIIT 프로토콜로 총 4분만에 완료됩니다.\n버피테스트, 스프린트, 점프 스쿼트, 산악 달리기처럼 전신을 쓰는 동작이 HIIT에 가장 적합합니다.\n고강도 특성상 관절과 심혈관계에 부담이 크므로 주 2~3회를 초과하지 않고 충분한 회복 시간을 두어야 합니다.\n처음 시작하는 분은 강도를 60~70%로 낮추고, 기초 체력이 쌓인 후 점진적으로 강도를 높여가는 것이 안전합니다.", "tags": ["HIIT", "인터벌트레이닝", "고강도운동", "다이어트"]},
]

router = APIRouter(prefix="/admin", tags=["admin"])

BAN_DURATIONS = {
    "3d": timedelta(days=3),
    "3w": timedelta(weeks=3),
    "3m": timedelta(days=90),
    "3y": timedelta(days=1095),
    "permanent": timedelta(days=365 * 100),
}


class BanRequest(BaseModel):
    user_id: int
    duration: str
    reason: str


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "is_dormant": user.is_dormant,
        "banned_until": user.banned_until.isoformat() if user.banned_until else None,
        "ban_reason": user.ban_reason,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search:
        query = query.filter(
            or_(User.email.ilike(f"%{search}%"), User.nickname.ilike(f"%{search}%"))
        )
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [serialize_user(u) for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@router.post("/users/ban")
def ban_user(
    data: BanRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if data.duration not in BAN_DURATIONS:
        raise HTTPException(status_code=400, detail="유효하지 않은 정지 기간입니다.")

    user = db.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user.is_admin:
        raise HTTPException(status_code=403, detail="관리자 계정은 정지할 수 없습니다.")

    user.banned_until = datetime.now(timezone.utc) + BAN_DURATIONS[data.duration]
    user.ban_reason = data.reason
    db.commit()
    return {"message": f"{user.nickname} 계정이 정지되었습니다."}


@router.post("/users/{user_id}/unban")
def unban_user(
    user_id: int,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    user.banned_until = None
    user.ban_reason = None
    db.commit()
    return {"message": "계정 정지가 해제되었습니다."}


@router.delete("/posts/{post_id}", status_code=204)
def admin_delete_post(
    post_id: int,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post.is_deleted = True
    db.commit()


@router.get("/content")
def list_content(
    board_type: Optional[str] = Query(None),
    crawl_status: Optional[str] = Query("draft"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """크롤링된 게시물 목록 (관리자용)"""
    query = db.query(Post).filter(Post.is_crawled.is_(True), Post.is_deleted.is_(False))
    if board_type:
        query = query.filter(Post.board_type == board_type)
    if crawl_status:
        query = query.filter(Post.crawl_status == crawl_status)

    total = query.count()
    posts = query.order_by(Post.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "summary": p.summary,
                "source_url": p.source_url,
                "board_type": p.board_type,
                "tags": p.tags or [],
                "crawl_status": p.crawl_status,
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@router.post("/content/{post_id}/publish")
def publish_content(post_id: int, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """크롤링 게시물 게시 승인"""
    post = db.get(Post, post_id)
    if not post or not post.is_crawled:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post.crawl_status = "published"
    db.commit()
    return {"message": "게시되었습니다."}


@router.post("/content/{post_id}/reject")
def reject_content(post_id: int, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """크롤링 게시물 거절"""
    post = db.get(Post, post_id)
    if not post or not post.is_crawled:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post.crawl_status = "rejected"
    db.commit()
    return {"message": "거절되었습니다."}


@router.post("/content/seed")
def seed_content(_: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """테스트용 샘플 데이터 생성 (건강 10개 + 운동 10개)"""
    from app.services.crawler import get_or_create_crawler_user

    crawler_user = get_or_create_crawler_user(db)
    added = 0

    for item in _SEED_HEALTH:
        if not db.query(Post).filter(Post.title == item["title"]).first():
            db.add(Post(
                title=item["title"],
                content=item["summary"],
                summary=item["summary"],
                board_type="health",
                author_id=crawler_user.id,
                tags=item["tags"],
                is_crawled=True,
                crawl_status="draft",
            ))
            added += 1

    for item in _SEED_EXERCISE:
        if not db.query(Post).filter(Post.title == item["title"]).first():
            db.add(Post(
                title=item["title"],
                content=item["summary"],
                summary=item["summary"],
                board_type="exercise",
                author_id=crawler_user.id,
                tags=item["tags"],
                is_crawled=True,
                crawl_status="draft",
            ))
            added += 1

    db.commit()
    return {"message": f"샘플 데이터 {added}개 추가됨", "total": added}


@router.get("/crawl/status")
def get_crawl_status(_: User = Depends(get_admin_user)):
    """현재 크롤링 실행 여부"""
    from app.services.crawler import is_crawling
    return {"running": is_crawling()}


@router.post("/crawl/stop")
def stop_crawl(_: User = Depends(get_admin_user)):
    """실행 중인 크롤링 중단 요청"""
    from app.services.crawler import is_crawling, request_stop
    if not is_crawling():
        return {"message": "실행 중인 크롤링이 없습니다."}
    request_stop()
    return {"message": "크롤링 중단을 요청했습니다. 현재 키워드 처리 후 종료됩니다."}


@router.post("/crawl/{board_type}")
async def trigger_crawl(
    board_type: str,
    _: User = Depends(get_admin_user),
):
    """관리자용 수동 크롤링 실행 (health | exercise)"""
    if board_type not in ("health", "exercise"):
        raise HTTPException(status_code=400, detail="board_type은 health 또는 exercise여야 합니다.")

    from app.core.config import settings

    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail=".env에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 입력해 주세요.",
        )

    from app.services.crawler import is_crawling, run_crawl

    if is_crawling():
        raise HTTPException(status_code=409, detail="이미 크롤링이 실행 중입니다.")

    result = await run_crawl(board_type)
    return {
        "message": "크롤링 완료" if not result["stopped"] else "크롤링 중단됨",
        "board_type": board_type,
        **result,
    }


@router.get("/stats")
def get_stats(_: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()
    total_users = db.query(func.count(User.id)).scalar()
    new_today = db.query(func.count(User.id)).filter(func.date(User.created_at) == today).scalar()
    total_posts = db.query(func.count(Post.id)).filter(Post.is_deleted.is_(False)).scalar()
    banned = (
        db.query(func.count(User.id))
        .filter(User.banned_until > datetime.now(timezone.utc))
        .scalar()
    )
    return {
        "total_users": total_users,
        "new_users_today": new_today,
        "total_posts": total_posts,
        "banned_users": banned,
    }
