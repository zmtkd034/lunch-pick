// L14: 버튼을 누르면 포크가 오른쪽 위에서 대각선으로 날아와 버튼 오른쪽 위에 꽂힌 뒤 바로 사라진다(PRD R17).
// 선택이 유지되는 탭·칩의 포크는 CSS(선택된 동안 꽂혀 있음)로 처리하므로 여기서는 제외한다.
// 장식용이라 화면 읽기 프로그램에는 숨기고, 화면 상태(React)와 분리해 문서에 직접 붙였다가 지운다.
const FLY_MS = 520
const STAY_MS = 120
const FADE_MS = 160
// 포크 그림의 가로:세로 비율(public/fork.svg의 viewBox 20×60).
const FORK_RATIO = 20 / 60

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
}

function throwFork(button) {
  const rect = button.getBoundingClientRect()
  // 버튼 높이에 맞춘 포크 길이(작은 버튼 28px ~ 큰 버튼 44px).
  const height = Math.round(Math.min(44, Math.max(28, rect.height * 1.15)))
  const width = Math.round(height * FORK_RATIO)
  // 갈퀴 끝이 박히는 자리: 버튼 오른쪽 위 모서리 조금 안쪽.
  const tipX = rect.right - Math.min(14, rect.width / 4)
  const tipY = rect.top + Math.min(6, rect.height / 4)

  const fork = document.createElement('img')
  fork.src = '/fork.svg'
  fork.alt = ''
  fork.className = 'fork-throw'
  fork.setAttribute('aria-hidden', 'true')
  fork.width = width
  fork.height = height
  // 그림의 아래 가운데(갈퀴 끝)가 박히는 자리에 오도록 놓고, 그 점을 기준으로 돌린다.
  fork.style.left = `${tipX - width / 2}px`
  fork.style.top = `${tipY - height}px`
  document.body.appendChild(fork)
  setTimeout(() => fork.remove(), FLY_MS + STAY_MS + FADE_MS + 200)
}

// 문서 전체의 버튼 클릭에 효과를 건다. 돌려준 함수를 부르면 효과를 해제한다.
export function installForkEffect() {
  function handleClick(event) {
    const button = event.target.closest?.('button')
    if (!button || button.disabled || button.closest('.mode-tabs') || prefersReducedMotion()) {
      return
    }
    throwFork(button)
  }
  document.addEventListener('click', handleClick)
  return () => document.removeEventListener('click', handleClick)
}
