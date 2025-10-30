import DocTransLogo from '@/components/DocTransLogo';
import { Card, CardContent } from '@/components/ui/card';
import { Mail } from 'lucide-react';
import Link from 'next/link';

export default function Contact() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-[#171717] to-[#000000]">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12 space-y-4">
          <Link href="/" className="inline-block mb-4 hover:opacity-80 transition-opacity">
            <DocTransLogo size="md" className="text-white" />
          </Link>
          <h1 className="text-4xl font-bold text-white">Contact Us</h1>
          <p className="text-gray-400">We're here to help</p>
        </div>

        {/* Content */}
        <Card className="bg-[#1f1f1f]/50 border-gray-800 backdrop-blur-sm">
          <CardContent className="p-8 space-y-8 text-gray-300">

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">Get in Touch</h2>
              <p className="leading-relaxed">
                Have questions, feedback, or need assistance? We'd love to hear from you!
                Our support team is ready to help with any questions about DocTrans.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">Support Email</h2>
              <div className="bg-[#2a2a2a] border border-gray-700 rounded-lg p-6 flex items-center space-x-4">
                <div className="bg-gradient-to-r from-[#fbbf24] to-[#f97316] p-3 rounded-lg">
                  <Mail className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-gray-400 text-sm mb-1">Email us at</p>
                  <a
                    href="mailto:support@nexmind.com"
                    className="text-[#fbbf24] hover:text-[#f97316] text-lg font-semibold transition-colors"
                  >
                    support@nexmind.com
                  </a>
                </div>
              </div>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">What We Can Help With</h2>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Technical support and troubleshooting</li>
                <li>Questions about translation quality or formatting</li>
                <li>Account and billing inquiries</li>
                <li>Feature requests and suggestions</li>
                <li>Partnership and business opportunities</li>
                <li>General feedback about DocTrans</li>
              </ul>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Response Time</h2>
              <p className="leading-relaxed">
                We typically respond to all inquiries within 24-48 hours during business days.
                For urgent matters, please mention "Urgent" in your email subject line.
              </p>
            </section>

            <section className="space-y-3 bg-[#2a2a2a] border border-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white">Before You Contact Us</h3>
              <p className="leading-relaxed text-sm">
                Please check our{' '}
                <Link href="/privacy" className="text-[#fbbf24] hover:text-[#f97316] transition-colors">
                  Privacy Policy
                </Link>
                {' '}for information about how we handle your data. For general questions about how DocTrans works,
                you might find answers on our home page.
              </p>
            </section>

            <div className="pt-8 mt-8 border-t border-gray-700 text-center">
              <Link
                href="/"
                className="inline-block px-6 py-3 bg-gradient-to-r from-[#fbbf24] to-[#f97316] text-white font-semibold rounded-lg hover:shadow-lg hover:scale-105 transition-all"
              >
                Back to Home
              </Link>
            </div>

          </CardContent>
        </Card>
      </div>
    </main>
  );
}
