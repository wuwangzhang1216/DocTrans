import TranslationUpload from '@/components/TranslationUpload';
import TranslationHistory from '@/components/TranslationHistory';
import DocTransLogo from '@/components/DocTransLogo';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-[#171717] to-[#000000]">
      <div className="container mx-auto px-4 py-16 max-w-6xl">
        {/* Hero Section */}
        <div className="text-center mb-16 space-y-6">
          <div className="flex justify-center mb-4">
            <DocTransLogo size="lg" className="text-white" />
          </div>
          <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto">
            AI-powered translation that preserves your document's formatting and layout
          </p>
        </div>

        {/* Upload Section */}
        <TranslationUpload />

        {/* History Section */}
        <TranslationHistory />

        {/* Features Section */}
        <div className="mt-32 max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
            {/* Feature Item */}
            <div className="text-center space-y-3 group">
              <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-[#fbbf24] to-[#f97316] flex items-center justify-center transform group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold">Multiple Formats</h3>
              <p className="text-gray-400 text-sm leading-relaxed">PDF, DOCX, PPTX, TXT, and Markdown</p>
            </div>

            <div className="text-center space-y-3 group">
              <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-[#fbbf24] to-[#f97316] flex items-center justify-center transform group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
              </div>
              <h3 className="text-white font-semibold">Format Preservation</h3>
              <p className="text-gray-400 text-sm leading-relaxed">Original layout and styling intact</p>
            </div>

            <div className="text-center space-y-3 group">
              <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-[#fbbf24] to-[#f97316] flex items-center justify-center transform group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold">Lightning Fast</h3>
              <p className="text-gray-400 text-sm leading-relaxed">Get your translations in seconds</p>
            </div>

            <div className="text-center space-y-3 group">
              <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-[#fbbf24] to-[#f97316] flex items-center justify-center transform group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold">Real-time Progress</h3>
              <p className="text-gray-400 text-sm leading-relaxed">Live translation status updates</p>
            </div>

            <div className="text-center space-y-3 group">
              <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-[#fbbf24] to-[#f97316] flex items-center justify-center transform group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                </svg>
              </div>
              <h3 className="text-white font-semibold">11 Languages</h3>
              <p className="text-gray-400 text-sm leading-relaxed">Chinese, Spanish, French, and more</p>
            </div>

            <div className="text-center space-y-3 group">
              <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-[#fbbf24] to-[#f97316] flex items-center justify-center transform group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold">Secure & Private</h3>
              <p className="text-gray-400 text-sm leading-relaxed">Auto-deleted after completion</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-24 pb-8 text-center border-t border-gray-800 pt-8">
          <div className="space-y-4">
            <div className="flex justify-center space-x-6 text-sm">
              <Link
                href="/about"
                className="text-gray-400 hover:text-white transition-colors"
              >
                About Us
              </Link>
              <Link
                href="/contact"
                className="text-gray-400 hover:text-white transition-colors"
              >
                Contact
              </Link>
              <Link
                href="/privacy"
                className="text-gray-400 hover:text-white transition-colors"
              >
                Privacy Policy
              </Link>
            </div>
            <p className="text-gray-500 text-xs">
              © {new Date().getFullYear()} DocTrans. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </main>
  );
}