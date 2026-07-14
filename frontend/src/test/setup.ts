import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock do fetch global
global.fetch = vi.fn()

// Mock do FileReader
global.FileReader = class MockFileReader {
  onload: ((event: { target: { result: string } }) => void) | null = null
  onerror: (() => void) | null = null
  result: string | ArrayBuffer = ''

  readAsDataURL(_file: File) {
    setTimeout(() => {
      this.result = 'data:image/png;base64,fake'
      if (this.onload) {
        this.onload({ target: { result: this.result as string } })
      }
    }, 0)
  }
} as unknown as typeof FileReader

// Mock do matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
