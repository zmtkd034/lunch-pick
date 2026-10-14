// L17: 카드 뒷면. 물음표만 두고, 두근거리는 접시·반짝이·떠오르는 작은 물음표·빛줄기로 기대감을 준다.
// 식당 뽑기와 메뉴 뽑기가 같이 쓴다. 꾸밈은 모두 장식이라 화면 읽기 프로그램에는 숨긴다.
export default function CardBack({ hidden }) {
  return (
    <div className="card-face card-back" aria-hidden={hidden}>
      <span className="card-shine" />
      <span className="card-sparkle sparkle-1" />
      <span className="card-sparkle sparkle-2" />
      <span className="card-sparkle sparkle-3" />
      <span className="card-sparkle sparkle-4" />
      <span className="card-mini mini-1">?</span>
      <span className="card-mini mini-2">?</span>
      <span className="card-mini mini-3">?</span>
      <span className="card-mark">?</span>
    </div>
  )
}
