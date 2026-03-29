/**
 * useGridKeyboardNav tests
 */

import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useGridKeyboardNav } from './useGridKeyboardNav'

describe('useGridKeyboardNav', () => {
    it('should initialize with null focused cell', () => {
        const { result } = renderHook(() =>
            useGridKeyboardNav({ rows: 3, cols: 3 })
        )
        expect(result.current.focusedCell).toBeNull()
    })

    it('should generate correct cell props', () => {
        const { result } = renderHook(() =>
            useGridKeyboardNav({ rows: 3, cols: 3 })
        )

        const cellProps = result.current.getCellProps(1, 2)

        expect(cellProps['data-row']).toBe(1)
        expect(cellProps['data-col']).toBe(2)
        expect(cellProps.role).toBe('gridcell')
        expect(cellProps.tabIndex).toBe(-1) // Not focused initially
    })

    it('should update focused cell on focus', () => {
        const { result } = renderHook(() =>
            useGridKeyboardNav({ rows: 3, cols: 3 })
        )

        const cellProps = result.current.getCellProps(1, 2)

        act(() => {
            cellProps.onFocus()
        })

        expect(result.current.focusedCell).toEqual({ row: 1, col: 2 })
    })

    it('should provide grid props with correct role', () => {
        const { result } = renderHook(() =>
            useGridKeyboardNav({ rows: 3, cols: 3 })
        )

        const gridProps = result.current.getGridProps()

        expect(gridProps.role).toBe('grid')
        expect(gridProps['aria-label']).toBeDefined()
    })
})
