'use client'

import { useEffect, useRef } from 'react'

interface GoogleAdProps {
  /**
   * 广告单元 ID (data-ad-slot)
   */
  adSlot?: string

  /**
   * 广告格式，默认为 'auto' (响应式)
   */
  adFormat?: 'auto' | 'fluid' | 'rectangle' | 'vertical' | 'horizontal'

  /**
   * 是否显示广告
   */
  show?: boolean

  /**
   * 自定义样式类名
   */
  className?: string

  /**
   * 广告容器的最小高度
   */
  minHeight?: string
}

/**
 * Google AdSense 响应式广告组件
 *
 * 使用前需要：
 * 1. 在 .env.local 中配置 NEXT_PUBLIC_ADSENSE_ID
 * 2. 在 layout.tsx 中添加 AdSense script
 *
 * @example
 * <GoogleAd
 *   adSlot="1234567890"
 *   show={jobStatus === 'processing'}
 * />
 */
export default function GoogleAd({
  adSlot,
  adFormat = 'auto',
  show = true,
  className = '',
  minHeight = '100px'
}: GoogleAdProps) {
  const adRef = useRef<HTMLDivElement>(null)
  const adSenseId = process.env.NEXT_PUBLIC_ADSENSE_ID

  useEffect(() => {
    // 如果不显示广告或没有配置 AdSense ID，则不渲染
    if (!show || !adSenseId) {
      return
    }

    try {
      // 推送广告到 AdSense
      if (typeof window !== 'undefined') {
        // @ts-ignore
        ;(window.adsbygoogle = window.adsbygoogle || []).push({})
      }
    } catch (error) {
      console.error('Google AdSense 加载失败:', error)
    }
  }, [show, adSenseId])

  // 如果不显示或没有配置，返回 null
  if (!show || !adSenseId) {
    return null
  }

  return (
    <div className={`google-ad-container ${className}`}>
      {/* 广告标签 */}
      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1 text-center">
        广告
      </div>

      {/* 广告容器 */}
      <div
        ref={adRef}
        className="ad-wrapper rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50"
        style={{ minHeight }}
      >
        <ins
          className="adsbygoogle"
          style={{
            display: 'block',
            minHeight: minHeight,
          }}
          data-ad-client={adSenseId}
          data-ad-slot={adSlot}
          data-ad-format={adFormat}
          data-full-width-responsive="true"
        />
      </div>
    </div>
  )
}
