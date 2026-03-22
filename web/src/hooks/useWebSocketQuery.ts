import { useState, useCallback, useEffect, useRef } from 'react'
import { apiClient } from '@/services/api-client'
import type { QueryRequest, WebSocketMessage } from '@/types/api'
import { readAgenticQuerySnapshot, writeAgenticQuerySnapshot } from '@/lib/agenticQuerySession'

interface UseWebSocketQueryState {
  messages: WebSocketMessage[]
  isConnected: boolean
  isLoading: boolean
  error: string | null
}

function initialWsState(): UseWebSocketQueryState {
  const s = readAgenticQuerySnapshot()
  return {
    messages: s?.wsMessages ?? [],
    isConnected: false,
    isLoading: false,
    error: s?.wsError ?? null,
  }
}

export function useWebSocketQuery() {
  const [state, setState] = useState<UseWebSocketQueryState>(initialWsState)

  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback((queryRequest: QueryRequest) => {
    writeAgenticQuerySnapshot({ wsMessages: [], wsError: null })
    setState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
      messages: [],
    }))

    try {
      const ws = apiClient.connectWebSocket(
        queryRequest,
        (message: WebSocketMessage) => {
          setState(prev => {
            const newState = {
              ...prev,
              messages: [...prev.messages, message],
              isConnected: true,
            }
            
            // Set isLoading to false when answer arrives
            if (message.type === 'answer') {
              newState.isLoading = false
            }
            
            // Close connection when complete
            if (message.type === 'complete' && ws) {
              ws.close()
            }
            
            return newState
          })
        },
        (error: Event) => {
          setState(prev => ({
            ...prev,
            error: 'WebSocket connection error',
            isConnected: false,
            isLoading: false,
          }))
        },
        () => {
          setState(prev => ({
            ...prev,
            isConnected: false,
          }))
        }
      )

      wsRef.current = ws
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to connect',
        isLoading: false,
      }))
    }
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setState(prev => ({
      ...prev,
      isConnected: false,
    }))
  }, [])

  const reset = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setState({
      messages: [],
      isConnected: false,
      isLoading: false,
      error: null,
    })
  }, [])

  useEffect(() => {
    writeAgenticQuerySnapshot({
      wsMessages: state.messages,
      wsError: state.error,
    })
  }, [state.messages, state.error])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    ...state,
    connect,
    disconnect,
    reset,
  }
}
