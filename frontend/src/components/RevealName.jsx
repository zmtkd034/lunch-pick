// L22: 뽑힌 이름(식당·메뉴)을 "띠용" 하고 튀어나왔다가 제자리로 돌아오게 강조한다.
// 부모가 뽑을 때마다 key를 바꿔 새로 그리므로 같은 결과가 연속으로 나와도 애니메이션이 다시 재생된다.
// "띠용!"은 장식이라 화면 읽기 프로그램에는 숨긴다.
export default function RevealName({ name }) {
  return (
    <span className="reveal-name">
      <strong className="card-name">{name}</strong>
      <span className="boing-burst" aria-hidden="true">
        띠용!
      </span>
    </span>
  )
}
