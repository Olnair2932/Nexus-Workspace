const path = require("path");
const fs = require("fs");
const { execFile } = require("child_process");
const express = require("express");
const multer = require("multer");
const dotenv = require("dotenv");

const WORKSPACE = path.resolve(__dirname, "..");

dotenv.config({
    path: path.join(WORKSPACE, ".env"),
    quiet: true
});

const app = express();
const PORT = process.env.PORT || 3003;

const HTML_DIR = path.join(WORKSPACE, "html");
const PUBLIC_DIR = path.join(HTML_DIR, "public");
const GERADOS_DIR = path.join(HTML_DIR, "html_gerados");
const UPLOADS_DIR = path.join(HTML_DIR, "uploads");
const PYTHON_DIR = path.join(WORKSPACE, "python");
const TOOLS_DIR = path.join(__dirname, "ferramentas");

const IA_TOOL = path.join(TOOLS_DIR, "nexus_ia.js");
const SHELL_TOOL = path.join(TOOLS_DIR, "nexus_shell.js");

// CRIA PASTAS BLINDADAS ~/workspace
for (const dir of [HTML_DIR, PUBLIC_DIR, GERADOS_DIR, UPLOADS_DIR, PYTHON_DIR, TOOLS_DIR]) {
    fs.mkdirSync(dir, { recursive: true });
}

app.use(express.json({ limit: "15mb" }));
app.use(express.urlencoded({ extended: true }));
app.use(express.static(PUBLIC_DIR));
app.use(express.static(HTML_DIR));
app.use("/html_gerados", express.static(GERADOS_DIR));
app.use("/uploads", express.static(UPLOADS_DIR));

function executarNode(arquivo, argumentos = []) {
    return new Promise((resolve) => {
        execFile(process.execPath, [arquivo, ...argumentos], {
            cwd: WORKSPACE, env: process.env, timeout: 120000, maxBuffer: 20 * 1024 * 1024
        }, (erro, stdout, stderr) => {
            resolve({ ok: !erro, codigo: erro ? (typeof erro.code === "number" ? erro.code : 1) : 0, stdout: stdout || "", stderr: stderr || "", erro: erro ? erro.message : "" });
        });
    });
}

function executarPython(comando) {
    return new Promise((resolve) => {
        execFile("sh", ["-c", comando], {
            cwd: WORKSPACE, env: process.env, timeout: 120000, maxBuffer: 20 * 1024 * 1024
        }, (erro, stdout, stderr) => {
            resolve({ ok: !erro, codigo: erro ? (typeof erro.code === "number" ? erro.code : 1) : 0, stdout: stdout || "", stderr: stderr || "", erro: erro ? erro.message : "" });
        });
    });
}

// UPLOAD
const storageImagem = multer.diskStorage({
    destination: function (req, file, cb) { cb(null, UPLOADS_DIR); },
    filename: function (req, file, cb) {
        const extensao = path.extname(file.originalname || "").toLowerCase();
        const nomeBase = path.basename(file.originalname || "imagem", extensao).replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 80);
        const nomeFinal = Date.now() + "_" + nomeBase + extensao;
        cb(null, nomeFinal);
    }
});
const uploadImagem = multer({
    storage: storageImagem,
    limits: { fileSize: 10 * 1024 * 1024 },
    fileFilter: function (req, file, cb) {
        if (file && file.mimetype && file.mimetype.startsWith("image/")) cb(null, true);
        else cb(new Error("Apenas arquivos de imagem são permitidos."));
    }
});

app.post("/api/html/upload", uploadImagem.single("imagem"), (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ ok: false, erro: "Nenhuma imagem foi enviada." });
        const url = "/uploads/" + encodeURIComponent(req.file.filename);
        return res.json({ ok: true, acao: "upload_imagem", arquivo: req.file.filename, url, tamanho: req.file.size, tipo: req.file.mimetype });
    } catch (erro) {
        return res.status(500).json({ ok: false, erro: "Erro ao processar imagem.", detalhe: erro.message });
    }
});

app.get("/", (req, res) => {
    res.sendFile(path.join(PUBLIC_DIR, "html_studio.html"));
});

app.get("/api/html/editar", async (req, res) => {
    const arquivoHTML = String(req.query.arquivo || "").trim();
    if (!arquivoHTML) return res.status(400).json({ ok: false, erro: "Arquivo não informado." });
    const nomeSeguro = path.basename(arquivoHTML);
    const indexFile = path.join(GERADOS_DIR, "index.json");
    if (!fs.existsSync(indexFile)) return res.status(404).json({ ok: false, erro: "Índice HTML não encontrado." });
    try {
        const dados = JSON.parse(fs.readFileSync(indexFile, "utf-8"));
        const pagina = (dados.paginas || []).find(item => item.arquivo === nomeSeguro);
        if (!pagina) return res.status(404).json({ ok: false, erro: "Página não encontrada." });
        const ferramentaDados = path.join(PYTHON_DIR, "ferramentas", "nexus_html_dados.py");
        if (!fs.existsSync(ferramentaDados)) {
            return res.json({ ok: true, acao: "editar", pagina: { ...pagina, preco: pagina.preco || "", descricao: pagina.descricao || "" } });
        }
        const resultado = await new Promise((resolve) => {
            execFile("python3", [ferramentaDados, nomeSeguro], { cwd: WORKSPACE, env: process.env, timeout: 120000, maxBuffer: 5 * 1024 * 1024 }, (erro, stdout, stderr) => {
                resolve({ ok: !erro, stdout: stdout || "", stderr: stderr || "", erro: erro ? erro.message : "" });
            });
        });
        let dadosHTML = {};
        try { dadosHTML = JSON.parse(resultado.stdout.trim()); } catch { dadosHTML = {}; }
        res.json({ ok: true, acao: "editar", pagina: { ...pagina, preco: dadosHTML.preco || pagina.preco || "", descricao: dadosHTML.descricao || pagina.descricao || "" } });
    } catch (erro) {
        res.status(500).json({ ok: false, erro: "Erro ao carregar página.", detalhe: erro.message });
    }
});

app.get("/api/html/listar", (req, res) => {
    try {
        const indexFile = path.join(GERADOS_DIR, "index.json");
        if (!fs.existsSync(indexFile)) return res.json({ ok: true, paginas: [] });
        const indice = JSON.parse(fs.readFileSync(indexFile, "utf-8"));
        res.json({ ok: true, paginas: indice.paginas || [] });
    } catch (e) { res.json({ ok: true, paginas: [] }); }
});

app.get("/api/htmls", (req, res) => {
    try {
        const files = fs.readdirSync(GERADOS_DIR).filter(f => f.endsWith(".html")).sort().reverse();
        res.json(files);
    } catch { res.json([]); }
});

app.post("/api/html/excluir", async (req, res) => {
    const arquivoHTML = String(req.body?.arquivo || "").trim();
    if (!arquivoHTML) return res.status(400).json({ ok: false, erro: "Arquivo não informado." });
    const nomeSeguro = path.basename(arquivoHTML);
    const ferramentaExcluir = path.join(PYTHON_DIR, "ferramentas", "nexus_html_excluir.py");
    if (!fs.existsSync(ferramentaExcluir)) {
        try { fs.unlinkSync(path.join(GERADOS_DIR, nomeSeguro)); } catch {}
        const indexFile = path.join(GERADOS_DIR, "index.json");
        if (fs.existsSync(indexFile)) {
            let indice = JSON.parse(fs.readFileSync(indexFile, "utf-8"));
            indice.paginas = (indice.paginas || []).filter(p => p.arquivo !== nomeSeguro);
            fs.writeFileSync(indexFile, JSON.stringify(indice, null, 2));
        }
        return res.json({ ok: true });
    }
    const resultado = await new Promise((resolve) => {
        execFile("python3", [ferramentaExcluir, nomeSeguro], { cwd: WORKSPACE, env: process.env, timeout: 120000, maxBuffer: 5 * 1024 * 1024 }, (erro, stdout, stderr) => {
            resolve({ ok: !erro, stdout: stdout || "", stderr: stderr || "", erro: erro ? erro.message : "" });
        });
    });
    try {
        const dados = JSON.parse(resultado.stdout.trim());
        if (!dados.ok) return res.status(400).json(dados);
        return res.json(dados);
    } catch {
        return res.status(500).json({ ok: false, erro: "A ferramenta de exclusão não retornou JSON válido.", stdout: resultado.stdout, stderr: resultado.stderr });
    }
});

app.post("/api/html/atualizar", async (req, res) => {
    const arquivoHTML = String(req.body?.arquivo || "").trim();
    const titulo = String(req.body?.titulo || "").trim();
    const preco = String(req.body?.preco || "").trim();
    const descricao = String(req.body?.descricao || "").trim();
    const imagem = String(req.body?.imagem || "").trim();
    if (!arquivoHTML) return res.status(400).json({ ok: false, erro: "Arquivo não informado." });
    const nomeSeguro = path.basename(arquivoHTML);
    const ferramentaDados = path.join(PYTHON_DIR, "ferramentas", "nexus_html_atualizar.py");
    if (!fs.existsSync(ferramentaDados)) {
        const indexFile = path.join(GERADOS_DIR, "index.json");
        if (fs.existsSync(indexFile)) {
            let indice = JSON.parse(fs.readFileSync(indexFile, "utf-8"));
            indice.paginas = (indice.paginas || []).map(p => p.arquivo === nomeSeguro ? { ...p, titulo, preco, descricao, imagem } : p);
            fs.writeFileSync(indexFile, JSON.stringify(indice, null, 2));
        }
        return res.json({ ok: true });
    }
    const resultado = await new Promise((resolve) => {
        const dadosAtualizacao = JSON.stringify({
            arquivo: nomeSeguro,
            titulo,
            preco,
            descricao,
            imagem
        });

        const processo = execFile(
            "python3",
            [ferramentaDados],
            {
                cwd: WORKSPACE,
                env: process.env,
                timeout: 120000,
                maxBuffer: 10 * 1024 * 1024
            },
            (erro, stdout, stderr) => {
                resolve({
                    ok: !erro,
                    stdout: stdout || "",
                    stderr: stderr || "",
                    erro: erro ? erro.message : ""
                });
            }
        );

        processo.stdin.write(dadosAtualizacao);
        processo.stdin.end();
    });

    try { const dados = JSON.parse(resultado.stdout.trim()); return res.json(dados); }
    catch { return res.status(500).json({ ok: false, erro: "A ferramenta de atualização não retornou JSON válido.", stdout: resultado.stdout, stderr: resultado.stderr }); }
});

// GERAR HTML COM GEMINI 3.1 LITE
app.post("/api/html/gerar", async (req, res) => {
    const nome = String(req.body?.nome || "").trim();
    const preco = String(req.body?.preco || "").trim();
    const descricao = String(req.body?.descricao || "").trim();
    const imagem = String(req.body?.imagem || "").trim();
    if (!nome) return res.status(400).json({ ok: false, erro: "Nome do produto não informado." });
    if (!preco) return res.status(400).json({ ok: false, erro: "Preço não informado." });
    if (!descricao) return res.status(400).json({ ok: false, erro: "Descrição não informada." });

    let solicitacao = `Crie um anúncio HTML profissional para o produto "${nome}".\nPreço: ${preco}\nDescrição:\n${descricao}\n\nREQUISITOS OBRIGATÓRIOS:\n- Criar uma página HTML completa.\n- Design moderno, profissional e responsivo.\n- Criar uma área de imagem do produto.\n- Criar botão "Comprar pelo WhatsApp".\n- Criar botão "Compartilhar página".\n- O botão WhatsApp deve funcionar.\n- O botão Compartilhar deve usar a API nativa navigator.share quando disponível.\n- Criar fallback de compartilhamento/cópia do endereço quando navigator.share não estiver disponível.\n- Não utilizar GEMINI_API_KEY no HTML.\n- Não colocar nenhuma chave de API no JavaScript do navegador.\n`;
    if (imagem) solicitacao += `\nA imagem real do produto está disponível nesta URL:\n${imagem}\nUse essa URL como imagem principal do produto no HTML.\n`;

    const gerador = path.join(PYTHON_DIR, "gerar_codigo.py");
    const resultado = await new Promise((resolve) => {
        execFile("python3", [gerador, solicitacao], { cwd: WORKSPACE, env: process.env, timeout: 180000, maxBuffer: 30 * 1024 * 1024 }, (erro, stdout, stderr) => {
            resolve({ ok: !erro, stdout: stdout || "", stderr: stderr || "", erro: erro ? erro.message : "" });
        });
    });

    if (!resultado.ok) {
        console.error("[NEXUS HTML GEMINI]", resultado.stderr || resultado.erro);
        return res.status(500).json({ ok: false, erro: "Falha ao gerar HTML com Gemini.", detalhe: resultado.stderr || resultado.erro, stdout: resultado.stdout });
    }

    const linhas = resultado.stdout.split(/\r?\n/).map(l => l.trim());
    const indiceSalvo = linhas.findIndex(l => l === "=== HTML SALVO ===");
    let arquivoGerado = "";
    if (indiceSalvo >= 0) arquivoGerado = linhas[indiceSalvo + 1] || "";
    if (!arquivoGerado) {
        const encontrados = linhas.filter(l => l.includes("html_gerados") && l.endsWith(".html"));
        arquivoGerado = encontrados.length ? encontrados[encontrados.length - 1] : "";
    }
    if (!arquivoGerado) return res.status(500).json({ ok: false, erro: "O Gemini gerou o HTML, mas o arquivo salvo não foi localizado.", stdout: resultado.stdout });

    const nomeArquivo = path.basename(arquivoGerado);
    fs.mkdirSync(GERADOS_DIR, { recursive: true });
    const indexFile = path.join(GERADOS_DIR, "index.json");
    let indice = { sistema: "NEXUS HTML STUDIO", versao: "1.0", modelo: "gemini-3.1-flash-lite", paginas: [] };
    if (fs.existsSync(indexFile)) {
        try { indice = JSON.parse(fs.readFileSync(indexFile, "utf-8")); } catch (e) { console.error("[NEXUS] Erro ao ler index.json:", e.message); }
    }
    if (!Array.isArray(indice.paginas)) indice.paginas = [];
    indice.paginas = indice.paginas.filter(p => p.arquivo !== nomeArquivo);
    indice.paginas.unshift({ arquivo: nomeArquivo, titulo: nome, preco, descricao, imagem, criado_em: new Date().toISOString() });
    fs.writeFileSync(indexFile, JSON.stringify(indice, null, 2), "utf-8");

    return res.json({ ok: true, arquivo: nomeArquivo, url: "/html_gerados/" + nomeArquivo, titulo: nome });
});

app.listen(PORT, "0.0.0.0", () => {
    console.log(`✅ NEXUS STUDIO gemini-3.1-flash-lite rodando http://127.0.0.1:${PORT}`);
    console.log(`WORKSPACE=${WORKSPACE}`);
    console.log(`PUBLIC=${PUBLIC_DIR}`);
    console.log(`GERADOS=${GERADOS_DIR}`);
    console.log(`UPLOADS=${UPLOADS_DIR}`);
});
