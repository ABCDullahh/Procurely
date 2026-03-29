/**
 * useGridKeyboardNav - Roving tabindex keyboard navigation for grid/table
 * 
 * Features:
 * - Arrow keys move focus by row/col
 * - Home/End navigate to first/last cell in row
 * - PageUp/PageDown jump rows
 * - Enter/Space trigger primary action
 * - Escape exits grid focus
 */

import { useCallback, useRef, useState, KeyboardEvent } from 'react'

interface UseGridKeyboardNavOptions {
    rows: number
    cols: number
    onActivate?: (row: number, col: number) => void
    onEscape?: () => void
}

interface GridPosition {
    row: number
    col: number
}

export function useGridKeyboardNav({
    rows,
    cols,
    onActivate,
    onEscape,
}: UseGridKeyboardNavOptions) {
    const [focusedCell, setFocusedCell] = useState<GridPosition | null>(null)
    const gridRef = useRef<HTMLTableElement | HTMLDivElement | null>(null)

    // Get cell element by position
    const getCellElement = useCallback(
        (row: number, col: number) => {
            if (!gridRef.current) return null
            return gridRef.current.querySelector(
                `[data-row="${row}"][data-col="${col}"]`
            ) as HTMLElement | null
        },
        []
    )

    // Focus a specific cell
    const focusCell = useCallback(
        (row: number, col: number) => {
            const clampedRow = Math.max(0, Math.min(rows - 1, row))
            const clampedCol = Math.max(0, Math.min(cols - 1, col))

            const cell = getCellElement(clampedRow, clampedCol)
            if (cell) {
                cell.focus()
                setFocusedCell({ row: clampedRow, col: clampedCol })
            }
        },
        [rows, cols, getCellElement]
    )

    // Handle keyboard events
    const handleKeyDown = useCallback(
        (e: KeyboardEvent<HTMLElement>) => {
            if (!focusedCell) return

            const { row, col } = focusedCell
            let handled = true

            switch (e.key) {
                case 'ArrowUp':
                    focusCell(row - 1, col)
                    break
                case 'ArrowDown':
                    focusCell(row + 1, col)
                    break
                case 'ArrowLeft':
                    focusCell(row, col - 1)
                    break
                case 'ArrowRight':
                    focusCell(row, col + 1)
                    break
                case 'Home':
                    if (e.ctrlKey) {
                        focusCell(0, 0)
                    } else {
                        focusCell(row, 0)
                    }
                    break
                case 'End':
                    if (e.ctrlKey) {
                        focusCell(rows - 1, cols - 1)
                    } else {
                        focusCell(row, cols - 1)
                    }
                    break
                case 'PageUp':
                    focusCell(Math.max(0, row - 5), col)
                    break
                case 'PageDown':
                    focusCell(Math.min(rows - 1, row + 5), col)
                    break
                case 'Enter':
                case ' ':
                    e.preventDefault()
                    onActivate?.(row, col)
                    break
                case 'Escape':
                    setFocusedCell(null)
                    onEscape?.()
                    break
                default:
                    handled = false
            }

            if (handled) {
                e.preventDefault()
                e.stopPropagation()
            }
        },
        [focusedCell, focusCell, rows, cols, onActivate, onEscape]
    )

    // Generate cell props
    const getCellProps = useCallback(
        (row: number, col: number) => {
            const isFocused = focusedCell?.row === row && focusedCell?.col === col
            return {
                'data-row': row,
                'data-col': col,
                tabIndex: isFocused ? 0 : -1,
                role: 'gridcell',
                'aria-selected': isFocused,
                onFocus: () => setFocusedCell({ row, col }),
                className: isFocused
                    ? 'ring-2 ring-ring ring-offset-2 ring-offset-background rounded'
                    : '',
            }
        },
        [focusedCell]
    )

    // Grid container props
    const getGridProps = useCallback(() => {
        return {
            ref: gridRef as React.RefObject<HTMLTableElement>,
            role: 'grid',
            'aria-label': 'Data grid with keyboard navigation',
            onKeyDown: handleKeyDown,
        }
    }, [handleKeyDown])

    // Initialize focus on first cell when entering grid
    const initFocus = useCallback(() => {
        if (!focusedCell && rows > 0 && cols > 0) {
            focusCell(0, 0)
        }
    }, [focusedCell, rows, cols, focusCell])

    return {
        focusedCell,
        setFocusedCell,
        getCellProps,
        getGridProps,
        focusCell,
        initFocus,
    }
}
