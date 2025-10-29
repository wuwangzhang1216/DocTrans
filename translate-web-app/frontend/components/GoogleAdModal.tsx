'use client'

import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

interface GoogleAdModalProps {
  /**
   * 广告单元 ID (data-ad-slot)
   */
  adSlot?: string

  /**
   * 是否显示模态广告
   */
  show: boolean

  /**
   * 关闭回调
   */
  onClose?: () => void

  /**
   * 是否显示关闭按钮（默认：true）
   */
  showCloseButton?: boolean

  /**
   * 翻译进度 (0-100)
   */
  progress?: number

  /**
   * 翻译状态
   */
  status?: 'queued' | 'processing' | 'completed' | 'failed'

  /**
   * 广告格式
   */
  adFormat?: 'auto' | 'fluid' | 'rectangle'
}

/**
 * Google AdSense 全屏弹窗广告组件
 *
 * 特点：
 * - 全屏模态显示
 * - 背景遮罩冻结主界面
 * - 根据翻译进度自动关闭
 * - 响应式设计
 *
 * @example
 * <GoogleAdModal
 *   show={isProcessing}
 *   progress={translationProgress}
 *   status={translationStatus}
 *   onClose={() => setShowAd(false)}
 * />
 */
export default function GoogleAdModal({
  adSlot,
  show,
  onClose,
  showCloseButton = true,
  progress = 0,
  status = 'processing',
  adFormat = 'auto'
}: GoogleAdModalProps) {
  const adRef = useRef<HTMLDivElement>(null)
  const adSenseId = process.env.NEXT_PUBLIC_ADSENSE_ID

  // 推送 AdSense 广告
  useEffect(() => {
    if (!show || !adSenseId) {
      return
    }

    try {
      // 延迟推送，确保 DOM 已渲染
      const timer = setTimeout(() => {
        if (typeof window !== 'undefined') {
          // @ts-ignore
          ;(window.adsbygoogle = window.adsbygoogle || []).push({})
        }
      }, 100)

      return () => clearTimeout(timer)
    } catch (error) {
      console.error('Google AdSense 加载失败:', error)
    }
  }, [show, adSenseId])

  // 处理关闭 - 只有在翻译完成或失败后才允许关闭
  const handleClose = () => {
    // 只有在非处理状态时才能关闭
    if (showCloseButton && status !== 'processing' && status !== 'queued') {
      onClose?.()
    }
  }

  // 阻止背景滚动
  useEffect(() => {
    if (show) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [show])

  // 如果不显示或没有配置，返回 null
  if (!show || !adSenseId) {
    return null
  }

  return (
    <>
      {/* 全屏遮罩层 - 磨砂玻璃效果，禁止点击关闭 */}
      <div
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-md animate-in fade-in duration-300 cursor-default"
      >
        {/* 模态内容容器 - 使用屏占比 80% 宽 × 60% 高，最大 1200px × 800px */}
        <div
          className="fixed left-1/2 top-1/2 z-50 w-[80vw] max-w-[1200px] -translate-x-1/2 -translate-y-1/2 animate-in zoom-in-95 duration-300"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 磨砂玻璃卡片 */}
          <div className="relative mx-4 rounded-3xl border border-white/20 bg-white/10 backdrop-blur-2xl p-6 shadow-2xl">
            {/* 关闭按钮 - 根据状态显示不同样式 */}
            {showCloseButton && (
              <button
                onClick={handleClose}
                disabled={status === 'processing' || status === 'queued'}
                className={`absolute right-6 top-6 rounded-xl p-3 backdrop-blur-sm transition-all duration-300 border-2 ${
                  status === 'processing' || status === 'queued'
                    ? 'bg-gray-600/30 text-gray-500 border-gray-600/50 cursor-not-allowed opacity-50'
                    : 'bg-green-500/80 text-white hover:bg-green-400 border-green-400 shadow-lg shadow-green-500/50 cursor-pointer animate-pulse'
                }`}
                aria-label={status === 'processing' || status === 'queued' ? '翻译中...' : '点击关闭'}
              >
                {status === 'processing' || status === 'queued' ? (
                  <svg className="h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <X className="h-5 w-5" />
                )}
              </button>
            )}

            {/* 广告内容区域 - 60vh 高度，最大 800px（符合 Google AdSense 规则） */}
            <div
              ref={adRef}
              className="ad-wrapper mt-4 h-[60vh] max-h-[800px] rounded-2xl overflow-hidden border border-white/20 bg-white/5 backdrop-blur-sm"
            >
              <ins
                className="adsbygoogle"
                style={{
                  display: 'block',
                  height: '100%',
                  minHeight: '400px',
                }}
                data-ad-client={adSenseId}
                data-ad-slot={adSlot}
                data-ad-format={adFormat}
                data-full-width-responsive="true"
              />
            </div>

            {/* 简洁进度条 */}
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-white/60">{progress}%</span>
              </div>
              <Progress value={progress} className="h-1.5 bg-white/20" />
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
