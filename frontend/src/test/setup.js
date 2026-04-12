import '@testing-library/jest-dom/vitest'
import React from 'react'

globalThis.React = React

// Provide deterministic element sizing so ResponsiveContainer can resolve dimensions in jsdom.
Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
	configurable: true,
	get() {
		return 960
	},
})

Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
	configurable: true,
	get() {
		return 540
	},
})

class ResizeObserverMock {
	observe() {}

	unobserve() {}

	disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverMock

const originalConsoleError = console.error
const originalConsoleWarn = console.warn

function isKnownRechartsSizeWarning(value) {
	const message = String(value || '')
	return message.includes('of chart should be greater than 0')
}

console.error = (...args) => {
	if (isKnownRechartsSizeWarning(args[0])) {
		return
	}

	originalConsoleError(...args)
}

console.warn = (...args) => {
	if (isKnownRechartsSizeWarning(args[0])) {
		return
	}

	originalConsoleWarn(...args)
}
