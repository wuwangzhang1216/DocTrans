import DocTransLogo from '@/components/DocTransLogo';
import { Card, CardContent } from '@/components/ui/card';
import Link from 'next/link';

export default function AboutUs() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-[#171717] to-[#000000]">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12 space-y-4">
          <Link href="/" className="inline-block mb-4 hover:opacity-80 transition-opacity">
            <DocTransLogo size="md" className="text-white" />
          </Link>
          <h1 className="text-4xl font-bold text-white">About Us</h1>
        </div>

        {/* Content */}
        <Card className="bg-[#1f1f1f]/50 border-gray-800 backdrop-blur-sm">
          <CardContent className="p-8 space-y-8 text-gray-300">

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Welcome to DocTrans</h2>
              <p className="leading-relaxed">
                DocTrans is a product of <span className="text-[#fbbf24] font-semibold">Nexmind Inc</span>,
                a company dedicated to making advanced AI technology accessible to everyone.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Our Mission</h2>
              <p className="leading-relaxed">
                We believe that language should never be a barrier to accessing information or conducting business.
                Our mission is to help people translate documents anytime, anywhere, while ensuring the highest quality
                translations and preserving the original document formatting.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">What We Do</h2>
              <p className="leading-relaxed">
                DocTrans is an AI-powered document translation service that supports multiple file formats including
                PDF, DOCX, PPTX, TXT, and Markdown. Unlike traditional translation tools that only handle plain text,
                we preserve your document's original structure, formatting, images, and layout.
              </p>
              <p className="leading-relaxed">
                Whether you're a student, professional, researcher, or business owner, DocTrans makes it easy to
                translate your documents with professional quality results in minutes.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Our Commitment</h2>
              <p className="leading-relaxed">
                We are committed to:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Delivering high-quality, accurate translations powered by advanced AI</li>
                <li>Preserving document formatting and structure</li>
                <li>Protecting your privacy and data security</li>
                <li>Providing fast, reliable service</li>
                <li>Continuously improving our technology to serve you better</li>
              </ul>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Why Choose DocTrans?</h2>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li><span className="text-white font-medium">Format Preservation:</span> Your documents look exactly the same after translation</li>
                <li><span className="text-white font-medium">AI-Powered Quality:</span> State-of-the-art language models ensure accurate translations</li>
                <li><span className="text-white font-medium">Multiple Formats:</span> Support for PDF, Word, PowerPoint, and more</li>
                <li><span className="text-white font-medium">Fast & Reliable:</span> Get your translated documents in minutes</li>
                <li><span className="text-white font-medium">Privacy First:</span> Your documents are automatically deleted after translation</li>
              </ul>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Get in Touch</h2>
              <p className="leading-relaxed">
                We'd love to hear from you! If you have questions, feedback, or suggestions, please visit our{' '}
                <Link href="/contact" className="text-[#fbbf24] hover:text-[#f97316] transition-colors">
                  Contact page
                </Link>.
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
