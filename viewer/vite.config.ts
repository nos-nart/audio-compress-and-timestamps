import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import fs from 'fs'
import path from 'path'

const outputDir = path.resolve(import.meta.dirname, '../output')

function serveFile(req: any, res: any, filePath: string, mime: string) {
  try {
    const stat = fs.statSync(filePath)
    res.setHeader('Accept-Ranges', 'bytes')
    res.setHeader('Content-Type', mime)

    const range = req.headers?.range
    if (range) {
      const match = range.match(/bytes=(\d+)-(\d*)/)
      if (match) {
        const start = Number(match[1])
        const end = match[2] ? Number(match[2]) : stat.size - 1
        const chunkSize = end - start + 1
        const stream = fs.createReadStream(filePath, { start, end })
        res.statusCode = 206
        res.setHeader('Content-Range', `bytes ${start}-${end}/${stat.size}`)
        res.setHeader('Content-Length', chunkSize)
        stream.pipe(res)
        return
      }
    }

    res.setHeader('Content-Length', stat.size)
    fs.createReadStream(filePath).pipe(res)
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

          if (req.url === '/save-transcription' && req.method === 'POST') {
            let body = ''
            req.on('data', (chunk: string) => { body += chunk })
            req.on('end', () => {
              try {
                const data = JSON.parse(body)
                const transDir = path.join(outputDir, 'transcription')
                fs.mkdirSync(transDir, { recursive: true })
                const stem = path.parse(data.file).name
                const filePath = path.join(transDir, `${stem}.json`)
                fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8')
                res.setHeader('Content-Type', 'application/json')
                res.end(JSON.stringify({ ok: true }))
              } catch {
                res.statusCode = 400
                res.end(JSON.stringify({ ok: false, error: 'save failed' }))
              }
            })
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
          serveFile(req, res, filePath, mime[ext] || 'application/octet-stream')
        })
      },
    },
  ],
})
