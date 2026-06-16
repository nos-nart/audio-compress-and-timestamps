import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import fs from 'fs'
import path from 'path'

const outputDir = path.resolve(import.meta.dirname, '../output')

function serveFile(res: any, filePath: string, mime: string) {
  try {
    const data = fs.readFileSync(filePath)
    res.setHeader('Content-Type', mime)
    res.end(data)
  } catch {
    res.statusCode = 404
    res.end('Not found')
  }
}

export default defineConfig({
  plugins: [
    vue(),
    UnoCSS(),
    {
      name: 'serve-output',
      configureServer(server) {
        server.middlewares.use('/api/', (req, res, next) => {
          if (req.url === '/list-recordings') {
            const audioDir = path.join(outputDir, 'audio')
            const transDir = path.join(outputDir, 'transcription')
            try {
              const audioFiles = fs.readdirSync(audioDir)
                .filter(f => f.endsWith('.ogg') || f.endsWith('.opus'))
                .map(f => path.parse(f).name)
              const transcriptions = fs.readdirSync(transDir)
                .filter(f => f.endsWith('.json'))
                .map(f => path.parse(f).name)
              const available = audioFiles.filter(f => transcriptions.includes(f))
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify(available))
            } catch {
              res.statusCode = 500
              res.end('[]')
            }
            return
          }
          next()
        })

        server.middlewares.use('/output/', (req, res) => {
          const filePath = path.join(outputDir, req.url || '')
          const ext = path.extname(filePath)
          const mime: Record<string, string> = {
            '.ogg': 'audio/ogg',
            '.opus': 'audio/ogg',
            '.json': 'application/json',
          }
          serveFile(res, filePath, mime[ext] || 'application/octet-stream')
        })
      },
    },
  ],
})
