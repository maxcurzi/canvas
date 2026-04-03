import {
  type ClientMessage,
  type ServerMessage,
  encodeClientMessage,
  decodeServerMessage,
} from './protocol'

export type ConnectionState = 'connecting' | 'connected' | 'disconnected'

export type WsClientOptions = {
  url: string
  onMessage: (msg: ServerMessage) => void
  onStateChange: (state: ConnectionState) => void
  reconnectIntervalMs?: number
}

export class WsClient {
  private ws: WebSocket | null = null
  private readonly url: string
  private readonly onMessage: (msg: ServerMessage) => void
  private readonly onStateChange: (state: ConnectionState) => void
  private readonly reconnectIntervalMs: number
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private intentionalClose = false

  constructor(options: WsClientOptions) {
    this.url = options.url
    this.onMessage = options.onMessage
    this.onStateChange = options.onStateChange
    this.reconnectIntervalMs = options.reconnectIntervalMs ?? 2000
  }

  connect(): void {
    this.intentionalClose = false
    this.onStateChange('connecting')
    this.ws = new WebSocket(this.url)
    this.ws.binaryType = 'arraybuffer'

    this.ws.onopen = () => {
      this.onStateChange('connected')
    }

    this.ws.onmessage = (event: MessageEvent) => {
      if (event.data instanceof ArrayBuffer) {
        try {
          const msg = decodeServerMessage(event.data)
          this.onMessage(msg)
        } catch (err) {
          console.error('Failed to decode server message:', err)
        }
      }
    }

    this.ws.onclose = () => {
      this.onStateChange('disconnected')
      if (!this.intentionalClose) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  send(msg: ClientMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(encodeClientMessage(msg))
    }
  }

  disconnect(): void {
    this.intentionalClose = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, this.reconnectIntervalMs)
  }
}
