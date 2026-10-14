// L13: 버튼을 누르면 포크(🍴)가 버튼을 찍고 바로 사라지는 효과(PRD R17).
// 선택이 유지되는 탭·칩의 포크는 CSS(선택된 동안 표시)로 처리하므로 여기서는 제외한다.
// 장식용이라 화면 읽기 프로그램에는 숨기고, 화면 상태(React)와 분리해 문서에 직접 붙였다가 지운다.
const POKE_MS = 650

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
}

function poke(button) {
  const rect = button.getBoundingClientRect()
  const fork = document.createElement('span')
  fork.className = 'fork-poke'
  fork.textContent = '🍴'
  fork.setAttribute('aria-hidden', 'true')
  fork.style.left = `${rect.left + rect.width / 2}px`
  fork.style.top = `${rect.top}px`
  document.body.appendChild(fork)
  // 애니메이션이 끝나면 지운다. 끝 이벤트가 오지 않는 경우를 대비해 시간으로도 지운다.
  const remove = () => fork.remove()
  fork.addEventListener('animationend', remove, { once: true })
  setTimeout(remove, POKE_MS + 200)
}

// 문서 전체의 버튼 클릭에 효과를 건다. 돌려준 함수를 부르면 효과를 해제한다.
export function installForkEffect() {
  function handleClick(event) {
    const button = event.target.closest?.('button')
    if (!button || button.disabled || button.closest('.mode-tabs') || prefersReducedMotion()) {
      return
    }
    poke(button)
  }
  document.addEventListener('click', handleClick)
  return () => document.removeEventListener('click', handleClick)
}
