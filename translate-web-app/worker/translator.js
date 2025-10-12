const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execPromise = promisify(exec);

class DocumentTranslator {
  constructor() {
    // Use the new modular translators package
    this.projectRoot = path.join(__dirname, '../..');
  }

  async translateDocument(inputPath, outputPath, targetLanguage, apiKey, onProgress) {
    try {
      // Create a temporary Python script that uses the translate_doc module
      const tempScriptPath = path.join(path.dirname(outputPath), 'temp_translate.py');

      const pythonScript = `
import sys
import os
import json
sys.path.insert(0, '${this.projectRoot.replace(/\\/g, '\\\\')}')

from translators import DocumentTranslator

# Initialize translator with dynamic worker allocation (256 max workers, up to 16 concurrent pages, 64 workers per page)
translator = DocumentTranslator(api_key="${apiKey}", model="gemini-2.0-flash-lite", max_workers=256)

# Translate document
result = translator.translate_document(
    input_path="${inputPath.replace(/\\/g, '\\\\')}",
    output_path="${outputPath.replace(/\\/g, '\\\\')}",
    target_language="${targetLanguage}"
)

if result:
    # Print success marker and output path in JSON format
    print("SUCCESS")
    if isinstance(result, tuple):
        # PDF returns (mono_path, dual_path)
        print(json.dumps({"mono": result[0], "dual": result[1]}))
    else:
        # Other formats return True
        print(json.dumps({"output": "${outputPath.replace(/\\/g, '\\\\')}"}))
else:
    print("FAILED")
`;

      await fs.writeFile(tempScriptPath, pythonScript);

      // Execute Python script
      return new Promise((resolve, reject) => {
        const pythonProcess = exec(`python "${tempScriptPath}"`, {
          maxBuffer: 10 * 1024 * 1024 // 10MB buffer
        });

        let stdout = '';
        let stderr = '';
        let lastProgress = 0;

        pythonProcess.stdout.on('data', (data) => {
          stdout += data;
          console.log('Python output:', data.toString());

          // Parse progress from output
          const lines = data.toString().split('\n');
          for (const line of lines) {
            if (line.includes('Processing') || line.includes('Translating') || line.includes('Completed')) {
              // Extract progress percentage if available
              const match = line.match(/(\d+)%/);
              if (match) {
                const progress = parseInt(match[1]);
                if (progress > lastProgress) {
                  lastProgress = progress;
                  if (onProgress) onProgress(progress / 100);
                }
              } else if (line.includes('page')) {
                // Extract page progress
                const pageMatch = line.match(/page (\d+)\/(\d+)/i);
                if (pageMatch) {
                  const current = parseInt(pageMatch[1]);
                  const total = parseInt(pageMatch[2]);
                  const progress = Math.round((current / total) * 100);
                  if (progress > lastProgress) {
                    lastProgress = progress;
                    if (onProgress) onProgress(progress / 100);
                  }
                }
              }
            }
          }
        });

        pythonProcess.stderr.on('data', (data) => {
          stderr += data;
        });

        pythonProcess.on('close', async (code) => {
          // Clean up temp script
          try {
            await fs.unlink(tempScriptPath);
          } catch (err) {
            console.error('Error deleting temp script:', err);
          }

          if (code === 0 && stdout.includes('SUCCESS')) {
            // Parse output paths from Python JSON output
            try {
              const lines = stdout.split('\n');
              const jsonLine = lines.find(line => line.trim().startsWith('{'));
              if (jsonLine) {
                const pathInfo = JSON.parse(jsonLine);
                resolve({ success: true, output: stdout, paths: pathInfo });
              } else {
                resolve({ success: true, output: stdout });
              }
            } catch (parseError) {
              // If JSON parsing fails, still succeed but without path info
              resolve({ success: true, output: stdout });
            }
          } else {
            reject(new Error(`Translation failed: ${stderr || stdout}`));
          }
        });

        pythonProcess.on('error', (error) => {
          reject(error);
        });
      });
    } catch (error) {
      throw new Error(`Translation error: ${error.message}`);
    }
  }

  async checkPythonDependencies() {
    try {
      const checkScript = `
import sys
import os
sys.path.insert(0, '${this.projectRoot.replace(/\\/g, '\\\\')}')
try:
    from translators import DocumentTranslator
    from google import genai
    import fitz
    import pptx
    import docx
    import pdfplumber
    import dotenv
    print("All dependencies installed")
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)
`;

      const { stdout, stderr } = await execPromise(`python -c "${checkScript}"`);

      if (stderr || !stdout.includes('All dependencies installed')) {
        throw new Error('Python dependencies not installed');
      }

      return true;
    } catch (error) {
      console.error('Dependency check failed:', error.message);
      console.log('Installing required Python packages...');

      // Try to install dependencies
      try {
        await execPromise('pip install google-genai pymupdf python-pptx python-docx pdfplumber reportlab python-dotenv');
        return true;
      } catch (installError) {
        throw new Error('Failed to install Python dependencies');
      }
    }
  }
}

module.exports = DocumentTranslator;
