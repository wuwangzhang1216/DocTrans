import DocTransLogo from '@/components/DocTransLogo';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

export default function PrivacyPolicy() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-[#171717] to-[#000000]">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12 space-y-4">
          <Link href="/" className="inline-block mb-4 hover:opacity-80 transition-opacity">
            <DocTransLogo size="md" className="text-white" />
          </Link>
          <h1 className="text-4xl font-bold text-white">Privacy Policy</h1>
          <p className="text-gray-400">Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>

        {/* Content */}
        <Card className="bg-[#1f1f1f]/50 border-gray-800 backdrop-blur-sm">
          <CardContent className="p-8 space-y-8 text-gray-300">

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Introduction</h2>
              <p className="leading-relaxed">
                Welcome to DocTrans. We are committed to protecting your privacy and ensuring the security of your documents.
                This Privacy Policy explains how we collect, use, and safeguard your information when you use our AI-powered
                document translation service.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Information We Collect</h2>
              <h3 className="text-lg font-medium text-white mt-4">Documents and Files</h3>
              <p className="leading-relaxed">
                When you use our service, we temporarily process the documents you upload for translation purposes.
                This includes:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Original document files (PDF, DOCX, PPTX, TXT, Markdown)</li>
                <li>Translated document files</li>
                <li>Document metadata (file names, file types, file sizes)</li>
              </ul>

              <h3 className="text-lg font-medium text-white mt-4">Usage Information</h3>
              <p className="leading-relaxed">
                We may collect information about how you interact with our service, including:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Translation requests (source and target languages)</li>
                <li>Translation history within your current session</li>
                <li>Technical information (browser type, IP address, timestamps)</li>
              </ul>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">How We Use Your Information</h2>
              <p className="leading-relaxed">
                We use the collected information solely for the following purposes:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Processing and delivering translation services</li>
                <li>Improving translation quality and service performance</li>
                <li>Maintaining service security and preventing abuse</li>
                <li>Analyzing usage patterns to enhance user experience</li>
              </ul>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Data Security and Retention</h2>

              <h3 className="text-lg font-medium text-white mt-4">Automatic Deletion</h3>
              <p className="leading-relaxed">
                Your privacy and security are our top priorities. All uploaded documents and translated files are
                <span className="text-[#fbbf24] font-semibold"> automatically deleted from our servers immediately after
                the translation is completed and delivered to you</span>. We do not retain copies of your documents.
              </p>

              <h3 className="text-lg font-medium text-white mt-4">Security Measures</h3>
              <p className="leading-relaxed">
                We implement industry-standard security measures to protect your data during processing, including:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Encrypted data transmission (HTTPS/SSL)</li>
                <li>Secure cloud storage during active translation</li>
                <li>Access controls and monitoring</li>
                <li>Regular security audits</li>
              </ul>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Third-Party Services</h2>
              <p className="leading-relaxed">
                Our translation service uses AI language models provided by trusted third-party services.
                These services may process your documents to generate translations. We only work with providers
                that maintain strict data protection standards and do not use your data for training purposes.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Cookies and Tracking</h2>
              <p className="leading-relaxed">
                We use minimal cookies and local storage for essential functionality, such as:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Maintaining your session during translation</li>
                <li>Storing your translation history temporarily in your browser</li>
                <li>Remembering your language preferences</li>
              </ul>
              <p className="leading-relaxed mt-2">
                We do not use advertising cookies or track you across other websites.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Your Rights</h2>
              <p className="leading-relaxed">
                You have the right to:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Access information about how your data is processed</li>
                <li>Request deletion of any personal information we may have (though we automatically delete documents)</li>
                <li>Opt-out of optional data collection</li>
                <li>Withdraw consent at any time</li>
              </ul>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Children's Privacy</h2>
              <p className="leading-relaxed">
                Our service is not directed to individuals under the age of 13. We do not knowingly collect
                personal information from children.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Changes to This Policy</h2>
              <p className="leading-relaxed">
                We may update this Privacy Policy from time to time to reflect changes in our practices or for
                legal and regulatory reasons. We will notify users of any material changes by updating the
                "Last updated" date at the top of this policy.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-2xl font-semibold text-white">Contact Us</h2>
              <p className="leading-relaxed">
                If you have any questions, concerns, or requests regarding this Privacy Policy or our data practices,
                please contact us through our support channels.
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
