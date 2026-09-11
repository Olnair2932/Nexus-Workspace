const crypto = require("crypto");
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

const CLOUDINARY_URL = String(
    process.env.CLOUDINARY_URL || ""
).trim();

function obterCloudinaryConfig() {
    if (!CLOUDINARY_URL) {
        return null;
    }

    try {
        const url = new URL(CLOUDINARY_URL);

        if (url.protocol !== "cloudinary:") {
            return null;
        }

        const apiKey = decodeURIComponent(url.username || "");
        const apiSecret = decodeURIComponent(url.password || "");
        const cloudName = String(url.hostname || "").trim();

        if (!apiKey || !apiSecret || !cloudName) {
            return null;
        }

        return {
            apiKey,
            apiSecret,
            cloudName
        };
    } catch {
        return null;
    }
}

async function excluirVideoCloudinary(publicId) {
    const config = obterCloudinaryConfig();

    if (!config) {
        return {
            ok: false,
            erro: "CLOUDINARY_URL não está configurada corretamente no servidor."
        };
    }

    publicId = String(publicId || "").trim();

    if (!publicId) {
        return {
            ok: false,
            erro: "public_id do vídeo não informado."
        };
    }

    try {
        const timestamp = Math.floor(Date.now() / 1000);

        const assinaturaBase =
            `public_id=${publicId}&timestamp=${timestamp}${config.apiSecret}`;

        const assinatura = crypto
            .createHash("sha1")
            .update(assinaturaBase)
            .digest("hex");

        const formulario = new URLSearchParams();

        formulario.append(
            "public_id",
            publicId
        );

        formulario.append(
            "timestamp",
            String(timestamp)
        );

        formulario.append(
            "api_key",
            config.apiKey
        );

        formulario.append(
            "signature",
            assinatura
        );

        const resposta = await fetch(
            `https://api.cloudinary.com/v1_1/${config.cloudName}/video/destroy`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/x-www-form-urlencoded"
                },
                body: formulario.toString()
            }
        );

        let dados = {};

        try {
            dados = await resposta.json();
        } catch (_) {
            dados = {};
        }

        if (!resposta.ok) {
            return {
                ok: false,
                status: resposta.status,
                erro:
                    dados?.error?.message ||
                    dados?.message ||
                    "Cloudinary não conseguiu excluir o vídeo.",
                resposta: dados
            };
        }

        if (
            dados.result &&
            dados.result !== "ok" &&
            dados.result !== "not found"
        ) {
            return {
                ok: false,
                erro:
                    "Cloudinary retornou um resultado inesperado ao excluir o vídeo.",
                resposta: dados
            };
        }

        return {
            ok: true,
            dados
        };
    } catch (erro) {
        return {
            ok: false,
            erro: erro.message
        };
    }
}

async function enviarVideoCloudinary(caminhoArquivo) {
    const config = obterCloudinaryConfig();

    if (!config) {
        return {
            ok: false,
            erro: "CLOUDINARY_URL não está configurada corretamente no servidor."
        };
    }

    if (!caminhoArquivo || !fs.existsSync(caminhoArquivo)) {
        return {
            ok: false,
            erro: "Arquivo de vídeo temporário não encontrado."
        };
    }

    try {
        const arquivo = fs.readFileSync(caminhoArquivo);

        const timestamp = Math.floor(Date.now() / 1000);

        const crypto = require("crypto");

        const assinaturaBase =
            `timestamp=${timestamp}${config.apiSecret}`;

        const assinatura = crypto
            .createHash("sha1")
            .update(assinaturaBase)
            .digest("hex");

        const formulario = new FormData();

        formulario.append(
            "file",
            new Blob([arquivo]),
            path.basename(caminhoArquivo)
        );

        formulario.append(
            "api_key",
            config.apiKey
        );

        formulario.append(
            "timestamp",
            String(timestamp)
        );

        formulario.append(
            "signature",
            assinatura
        );

        const resposta = await fetch(
            `https://api.cloudinary.com/v1_1/${config.cloudName}/video/upload`,
            {
                method: "POST",
                body: formulario
            }
        );

        let dados = {};

        try {
            dados = await resposta.json();
        } catch (_) {
            dados = {};
        }

        if (!resposta.ok) {
            return {
                ok: false,
                status: resposta.status,
                erro:
                    dados?.error?.message ||
                    dados?.message ||
                    "Cloudinary não conseguiu enviar o vídeo.",
                resposta: dados
            };
        }

        return {
            ok: true,
            dados
        };
    } catch (erro) {
        return {
            ok: false,
            erro: erro.message
        };
    }
}

async function gerarImagemCloudinary(prompt) {
    const config = obterCloudinaryConfig();

    if (!config) {
        return {
            ok: false,
            erro: "CLOUDINARY_URL não está configurada corretamente no servidor."
        };
    }

    const resposta = await fetch(
        `https://api.cloudinary.com/v2/generate/${config.cloudName}/text_to_image`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization":
                    "Basic " +
                    Buffer.from(
                        `${config.apiKey}:${config.apiSecret}`
                    ).toString("base64")
            },
            body: JSON.stringify({
                model: {
                    id: "nano-banana-2"
                },
                prompt: String(prompt || "").trim(),
                image_size: {
                    aspect_ratio: "4:3",
                    resolution: "1K"
                },
                target: {
                    target_type: "managed_asset"
                }
            })
        }
    );

    let dados = {};

    try {
        dados = await resposta.json();
    } catch (_) {
        dados = {};
    }

    if (!resposta.ok) {
        return {
            ok: false,
            status: resposta.status,
            erro:
                dados?.error?.message ||
                dados?.message ||
                "Cloudinary não conseguiu gerar a imagem.",
            resposta: dados
        };
    }

    return {
        ok: true,
        dados
    };
}

/**
 * Materializa uma imagem gerada pelo Cloudinary em /html/uploads/.
 * Isso permite que o fluxo existente de incorporação em Base64 seja preservado.
 */
async function materializarImagemCloudinary(urlImagem) {
    const config = obterCloudinaryConfig();

    if (!config) {
        return {
            ok: false,
            erro: "CLOUDINARY_URL não está configurada corretamente no servidor."
        };
    }

    let url;

    try {
        url = new URL(String(urlImagem || "").trim());
    } catch (_) {
        return {
            ok: false,
            erro: "URL da imagem inválida."
        };
    }

    if (url.protocol !== "https:") {
        return {
            ok: false,
            erro: "A imagem precisa utilizar uma URL HTTPS."
        };
    }

    if (url.hostname !== `res.cloudinary.com`) {
        return {
            ok: false,
            erro: "A imagem informada não pertence ao Cloudinary."
        };
    }

    try {
        const resposta = await fetch(url.toString());

        if (!resposta.ok) {
            return {
                ok: false,
                erro: `Cloudinary retornou HTTP ${resposta.status}.`
            };
        }

        const contentType = String(
            resposta.headers.get("content-type") || ""
        ).toLowerCase();

        if (!contentType.startsWith("image/")) {
            return {
                ok: false,
                erro: "O arquivo retornado pelo Cloudinary não é uma imagem."
            };
        }

        const dados = Buffer.from(await resposta.arrayBuffer());

        if (dados.length > 15 * 1024 * 1024) {
            return {
                ok: false,
                erro: "A imagem gerada ultrapassa o limite permitido de 15 MB."
            };
        }

        const extensoes = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/svg+xml": ".svg"
        };

        const extensao = extensoes[contentType] || ".png";

        const nomeArquivo =
            `generated_${Date.now()}_${crypto.randomBytes(6).toString("hex")}${extensao}`;

        const caminhoArquivo = path.join(UPLOADS_DIR, nomeArquivo);

        fs.writeFileSync(caminhoArquivo, dados);

        return {
            ok: true,
            url: `/uploads/${nomeArquivo}`,
            nome: nomeArquivo,
            contentType,
            tamanho: dados.length
        };
    } catch (erro) {
        console.error(
            "[NEXUS IMAGEM] Falha ao materializar imagem Cloudinary:",
            erro.message
        );

        return {
            ok: false,
            erro: "Não foi possível salvar a imagem gerada.",
            detalhe: erro.message
        };
    }
}
const STUDIO_AUTH_SECRET = process.env.NEXUS_STUDIO_AUTH_SECRET || "";
const NEXUS_STUDIO_ADMIN_UID = String(
    process.env.NEXUS_STUDIO_ADMIN_UID || ""
).trim();
const ACESSO_URL = "https://nexus-acesso.onrender.com";
const STUDIO_COOKIE = "nexus_studio_token";
const STUDIO_TOKEN_MAX_AGE = 600;

function base64urlDecode(valor) {
    const padding = "=".repeat((4 - (valor.length % 4)) % 4);
    return Buffer.from(valor + padding, "base64url");
}

function validarTokenStudio(token) {
    if (!STUDIO_AUTH_SECRET || !token) return null;

    try {
        const partes = String(token).split(".");
        if (partes.length !== 2) return null;

        const [parteDados, parteAssinatura] = partes;

        const assinaturaEsperada = crypto
            .createHmac("sha256", STUDIO_AUTH_SECRET)
            .update(parteDados)
            .digest();

        const assinaturaRecebida = base64urlDecode(parteAssinatura);

        if (
            assinaturaRecebida.length !== assinaturaEsperada.length ||
            !crypto.timingSafeEqual(
                assinaturaRecebida,
                assinaturaEsperada
            )
        ) {
            return null;
        }

        const payload = JSON.parse(
            base64urlDecode(parteDados).toString("utf8")
        );

        if (!payload.uid) return null;
        if (Number(payload.exp || 0) < Math.floor(Date.now() / 1000)) {
            return null;
        }

        return payload;
    } catch {
        return null;
    }
}

function obterCookie(req, nome) {
    const cookies = String(req.headers.cookie || "")
        .split(";")
        .map(item => item.trim());

    for (const cookie of cookies) {
        const indice = cookie.indexOf("=");

        if (indice === -1) continue;

        const chave = cookie.slice(0, indice);
        const valor = cookie.slice(indice + 1);

        if (chave === nome) {
            return decodeURIComponent(valor);
        }
    }

    return null;
}

function obterTokenStudio(req) {
    const tokenQuery = String(req.query?.nexus_token || "").trim();

    if (tokenQuery) {
        return tokenQuery;
    }

    return obterCookie(req, STUDIO_COOKIE);
}

function obterAutenticacaoStudio(req) {
    const token = obterTokenStudio(req);
    const payload = validarTokenStudio(token);

    if (!payload || !payload.uid) {
        return null;
    }

    return {
        token,
        uid: String(payload.uid),
        admin: Boolean(
            NEXUS_STUDIO_ADMIN_UID &&
            String(payload.uid) === NEXUS_STUDIO_ADMIN_UID
        )
    };
}

function paginaPertenceAoUsuario(pagina, autenticacao) {
    if (!pagina || !autenticacao) return false;

    if (autenticacao.admin) return true;

    return (
        pagina.uid &&
        String(pagina.uid) === String(autenticacao.uid)
    );
}

function obterPaginaDoUsuario(nomeArquivo, autenticacao) {
    const indexFile = path.join(GERADOS_DIR, "index.json");

    if (!fs.existsSync(indexFile)) {
        return {
            ok: false,
            status: 404,
            erro: "Índice HTML não encontrado."
        };
    }

    try {
        const dados = JSON.parse(
            fs.readFileSync(indexFile, "utf-8")
        );

        const pagina = (dados.paginas || []).find(
            item => item.arquivo === nomeArquivo
        );

        if (!pagina) {
            return {
                ok: false,
                status: 404,
                erro: "Página não encontrada."
            };
        }

        if (!paginaPertenceAoUsuario(pagina, autenticacao)) {
            return {
                ok: false,
                status: 403,
                erro: "Você não tem permissão para acessar este anúncio."
            };
        }

        return {
            ok: true,
            pagina
        };
    } catch (erro) {
        return {
            ok: false,
            status: 500,
            erro: "Erro ao ler o índice HTML.",
            detalhe: erro.message
        };
    }
}

function executarFirebaseMedia(argumentos = [], timeout = 120000) {
    return new Promise((resolve) => {
        execFile(
            "python3",
            [FIREBASE_MEDIA_TOOL, ...argumentos],
            {
                cwd: WORKSPACE,
                env: process.env,
                timeout,
                maxBuffer: 20 * 1024 * 1024
            },
            (erro, stdout, stderr) => {
                resolve({
                    ok: !erro,
                    codigo: erro
                        ? (typeof erro.code === "number" ? erro.code : 1)
                        : 0,
                    stdout: stdout || "",
                    stderr: stderr || "",
                    erro: erro ? erro.message : ""
                });
            }
        );
    });
}

function analisarRespostaFirebaseMedia(resultado) {
    const texto = String(resultado.stdout || "").trim();

    if (!texto) {
        return {};
    }

    try {
        return JSON.parse(texto);
    } catch (_) {
        return {
            mensagem: texto
        };
    }
}

async function salvarVideoFirebase(uid, videoId, dados) {
    if (!uid || !videoId) {
        return {
            ok: false,
            erro: "UID e ID do vídeo são obrigatórios."
        };
    }

    if (!fs.existsSync(FIREBASE_MEDIA_TOOL)) {
        return {
            ok: false,
            erro: "Ferramenta nexus_firebase_media.py não encontrada."
        };
    }

    const payload = JSON.stringify(dados || {});

    const resultado = await executarFirebaseMedia([
        "salvar",
        String(uid),
        String(videoId),
        payload
    ]);

    if (!resultado.ok) {
        console.error(
            "[NEXUS FIREBASE MEDIA] Falha ao salvar vídeo:",
            resultado.stderr || resultado.erro
        );

        return {
            ok: false,
            erro:
                resultado.stderr ||
                resultado.erro ||
                "Falha ao salvar vídeo no Firebase."
        };
    }

    return {
        ok: true,
        dados: analisarRespostaFirebaseMedia(resultado)
    };
}

async function listarVideosFirebase(uid) {
    if (!uid) {
        return {
            ok: false,
            erro: "UID não informado."
        };
    }

    if (!fs.existsSync(FIREBASE_MEDIA_TOOL)) {
        return {
            ok: false,
            erro: "Ferramenta nexus_firebase_media.py não encontrada."
        };
    }

    const resultado = await executarFirebaseMedia([
        "listar",
        String(uid)
    ]);

    if (!resultado.ok) {
        console.error(
            "[NEXUS FIREBASE MEDIA] Falha ao listar vídeos:",
            resultado.stderr || resultado.erro
        );

        return {
            ok: false,
            erro:
                resultado.stderr ||
                resultado.erro ||
                "Falha ao listar vídeos no Firebase."
        };
    }

    return {
        ok: true,
        dados: analisarRespostaFirebaseMedia(resultado)
    };
}

async function excluirVideoFirebase(uid, videoId) {
    if (!uid || !videoId) {
        return {
            ok: false,
            erro: "UID e ID do vídeo são obrigatórios."
        };
    }

    if (!fs.existsSync(FIREBASE_MEDIA_TOOL)) {
        return {
            ok: false,
            erro: "Ferramenta nexus_firebase_media.py não encontrada."
        };
    }

    const resultado = await executarFirebaseMedia([
        "excluir",
        String(uid),
        String(videoId)
    ]);

    if (!resultado.ok) {
        console.error(
            "[NEXUS FIREBASE MEDIA] Falha ao excluir vídeo:",
            resultado.stderr || resultado.erro
        );

        return {
            ok: false,
            erro:
                resultado.stderr ||
                resultado.erro ||
                "Falha ao excluir vídeo do Firebase."
        };
    }

    return {
        ok: true,
        dados: analisarRespostaFirebaseMedia(resultado)
    };
}

function registrarUsoStudio(tipo, token) {
    if (!token || !validarTokenStudio(token)) {
        const erro = new Error(
            "Autorização do Studio inválida ou expirada."
        );
        erro.codigo = "STUDIO_AUTH_INVALIDA";
        throw erro;
    }

    return fetch(`${ACESSO_URL}/api/studio/uso`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            token,
            tipo
        })
    })
    .then(async resposta => {
        if (!resposta.ok) {
            let dados = {};

            try {
                dados = await resposta.json();
            } catch (_) {
                dados = {};
            }

            if (
                resposta.status === 403 &&
                dados.limite_atingido === true
            ) {
                const erro = new Error(
                    dados.erro || `Limite de ${tipo} atingido.`
                );

                erro.codigo = "LIMITE_ATINGIDO";
                erro.limiteAtingido = true;
                erro.tipo = tipo;

                throw erro;
            }

            const erro = new Error(
                dados.erro ||
                `Falha ao registrar uso (${tipo}): HTTP ${resposta.status}`
            );

            erro.codigo = "REGISTRO_USO_FALHOU";
            erro.status = resposta.status;

            throw erro;
        }

        return true;
    })
    .catch(erro => {
        console.warn(
            `[STUDIO] Não foi possível registrar uso (${tipo}): ${erro.message}`
        );
        throw erro;
    });
}

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

const FIREBASE_RESTORE_TOOL = path.join(
  PYTHON_DIR,
  "ferramentas",
  "nexus_firebase_sync.py"
);

async function restaurarHTMLsFirebase() {
  try {
    if (!fs.existsSync(FIREBASE_RESTORE_TOOL)) {
      console.error(
        "[NEXUS FIREBASE] Ferramenta de restauração não encontrada:",
        FIREBASE_RESTORE_TOOL
      );

      return {
        ok: false,
        erro: "nexus_firebase_sync.py não encontrado."
      };
    }

    console.log("============================================");
    console.log("☁️ NEXUS — RESTAURAÇÃO FIREBASE");
    console.log("============================================");
    console.log("🔄 Verificando HTMLs salvos no Firebase...");

    const resultado = await new Promise((resolve) => {
      execFile(
        "python3",
        [FIREBASE_RESTORE_TOOL, "restaurar_todos"],
        {
          cwd: WORKSPACE,
          env: process.env,
          timeout: 180000,
          maxBuffer: 30 * 1024 * 1024
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
    });

    if (resultado.stdout) {
      console.log(
        "[NEXUS FIREBASE RESTORE]",
        resultado.stdout.trim()
      );
    }

    if (!resultado.ok) {
      console.error(
        "[NEXUS FIREBASE] Restauração não concluída:",
        resultado.stderr || resultado.erro
      );

      console.log(
        "⚠️ O NEXUS continuará iniciando normalmente."
      );

      return {
        ok: false,
        erro: resultado.stderr || resultado.erro
      };
    }

    console.log("✅ Restauração Firebase concluída.");

    return {
      ok: true,
      mensagem: resultado.stdout.trim()
    };

  } catch (erro) {
    console.error(
      "[NEXUS FIREBASE] Erro durante restauração:",
      erro.message
    );

    console.log(
      "⚠️ O NEXUS continuará iniciando normalmente."
    );

    return {
      ok: false,
      erro: erro.message
    };
  }
}


const FIREBASE_SYNC_TOOL = path.join(
  PYTHON_DIR,
  "ferramentas",
  "nexus_firebase_sync.py"
);

const FIREBASE_MEDIA_TOOL = path.join(
  PYTHON_DIR,
  "ferramentas",
  "nexus_firebase_media.py"
);


function incorporarImagensNoHTML(nomeArquivo) {
  try {
    const caminhoHTML = path.join(GERADOS_DIR, path.basename(nomeArquivo));

    if (!fs.existsSync(caminhoHTML)) {
      console.log("[NEXUS IMAGEM] HTML não encontrado:", caminhoHTML);
      return { ok: false, erro: "HTML não encontrado." };
    }

    let html = fs.readFileSync(caminhoHTML, "utf-8");
    let alteracoes = 0;

    html = html.replace(
      /(<img\b[^>]*\bsrc=["'])(\/uploads\/([^"']+))(["'][^>]*>)/gi,
      (trecho, inicio, url, nomeImagem, fim) => {
        try {
          const nomeSeguro = path.basename(decodeURIComponent(nomeImagem));
          const caminhoImagem = path.join(UPLOADS_DIR, nomeSeguro);

          if (!fs.existsSync(caminhoImagem)) {
            console.log(
              "[NEXUS IMAGEM] Arquivo não encontrado:",
              caminhoImagem
            );
            return trecho;
          }

          const extensao = path.extname(nomeSeguro).toLowerCase();

          const tipos = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml"
          };

          const mime = tipos[extensao] || "application/octet-stream";

          const dados = fs.readFileSync(caminhoImagem);
          const base64 = dados.toString("base64");
          const dataURI = `data:${mime};base64,${base64}`;

          alteracoes++;

          console.log(
            `[NEXUS IMAGEM] Incorporada: ${nomeSeguro} (${dados.length} bytes)`
          );

          return inicio + dataURI + fim;
        } catch (erro) {
          console.error(
            "[NEXUS IMAGEM] Erro ao incorporar imagem:",
            erro.message
          );
          return trecho;
        }
      }
    );

    fs.writeFileSync(caminhoHTML, html, "utf-8");

    console.log(
      `[NEXUS IMAGEM] ${alteracoes} imagem(ns) incorporada(s) em ${path.basename(nomeArquivo)}`
    );

    return {
      ok: true,
      alteracoes
    };
  } catch (erro) {
    console.error(
      "[NEXUS IMAGEM] Falha:",
      erro.message
    );

    return {
      ok: false,
      erro: erro.message
    };
  }
}

async function sincronizarHTMLFirebase(nomeArquivo) {
  try {
    const imagemPersistida = incorporarImagensNoHTML(nomeArquivo);

    if (!imagemPersistida.ok) {
      console.error(
        "[NEXUS FIREBASE] Não foi possível preparar as imagens:",
        imagemPersistida.erro
      );
    }

    if (!nomeArquivo) {
      return {
        ok: false,
        erro: "Nome do HTML não informado para sincronização."
      };
    }

    if (!fs.existsSync(FIREBASE_SYNC_TOOL)) {
      return {
        ok: false,
        erro: "Ferramenta nexus_firebase_sync.py não encontrada."
      };
    }

    const resultado = await new Promise((resolve) => {
      execFile(
        "python3",
        [FIREBASE_SYNC_TOOL, "salvar", path.basename(nomeArquivo)],
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
    });

    if (!resultado.ok) {
      console.error(
        "[NEXUS FIREBASE] Falha ao sincronizar:",
        resultado.stderr || resultado.erro
      );

      return {
        ok: false,
        erro: resultado.stderr || resultado.erro || "Falha na sincronização Firebase.",
        stdout: resultado.stdout
      };
    }

    console.log(
      "[NEXUS FIREBASE]",
      resultado.stdout.trim() || "HTML sincronizado."
    );

    return {
      ok: true,
      mensagem: resultado.stdout.trim()
    };

  } catch (erro) {
    console.error(
      "[NEXUS FIREBASE] Erro:",
      erro.message
    );

    return {
      ok: false,
      erro: erro.message
    };
  }
}


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

// GERAR IMAGEM COM CLOUDINARY
app.post("/api/imagem/gerar", async (req, res) => {
    const autenticacao = obterAutenticacaoStudio(req);

    if (!autenticacao) {
        return res.status(401).json({
            ok: false,
            erro: "Autorização do Studio inválida ou expirada."
        });
    }

    const prompt = String(req.body?.prompt || "").trim();

    if (!prompt) {
        return res.status(400).json({
            ok: false,
            erro: "Descreva a imagem que deseja gerar."
        });
    }

    if (prompt.length > 4000) {
        return res.status(400).json({
            ok: false,
            erro: "O prompt da imagem não pode ultrapassar 4000 caracteres."
        });
    }

    try {
        await registrarUsoStudio(
            "geracoes",
            autenticacao.token
        );
    } catch (erroUso) {
        if (erroUso.codigo === "LIMITE_ATINGIDO") {
            return res.status(403).json({
                ok: false,
                erro: erroUso.message,
                limite_atingido: true,
                tipo: "geracoes"
            });
        }

        return res.status(500).json({
            ok: false,
            erro: "Não foi possível registrar o uso da geração.",
            detalhe: erroUso.message
        });
    }

    try {
        const resultado = await gerarImagemCloudinary(prompt);

        if (!resultado.ok) {
            return res.status(resultado.status || 502).json({
                ok: false,
                erro: resultado.erro,
                resposta: resultado.resposta || {}
            });
        }

        return res.json({
            ok: true,
            uid: autenticacao.uid,
            imagem: resultado.dados
        });
    } catch (erro) {
        console.error(
            "[NEXUS CLOUDINARY] Falha ao gerar imagem:",
            erro.message
        );

        return res.status(500).json({
            ok: false,
            erro: "Erro ao gerar imagem com Cloudinary.",
            detalhe: erro.message
        });
    }
});

// MATERIALIZAR IMAGEM GERADA PELA IA
app.post("/api/imagem/materializar", async (req, res) => {
    const autenticacao = obterAutenticacaoStudio(req);

    if (!autenticacao) {
        return res.status(401).json({
            ok: false,
            erro: "Autorização do Studio inválida ou expirada."
        });
    }

    const urlImagem = String(req.body?.url || "").trim();

    if (!urlImagem) {
        return res.status(400).json({
            ok: false,
            erro: "URL da imagem não informada."
        });
    }

    try {
        const resultado = await materializarImagemCloudinary(urlImagem);

        if (!resultado.ok) {
            return res.status(400).json(resultado);
        }

        return res.json({
            ok: true,
            uid: autenticacao.uid,
            url: resultado.url,
            nome: resultado.nome,
            contentType: resultado.contentType,
            tamanho: resultado.tamanho
        });
    } catch (erro) {
        console.error(
            "[NEXUS IMAGEM] Erro ao materializar imagem:",
            erro.message
        );

        return res.status(500).json({
            ok: false,
            erro: "Erro ao preparar a imagem gerada pela IA.",
            detalhe: erro.message
        });
    }
});
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

const MIDIA_TEMP_DIR = path.join(WORKSPACE, "html", "uploads", ".tmp_video");

fs.mkdirSync(MIDIA_TEMP_DIR, { recursive: true });

const storageVideoTemporario = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, MIDIA_TEMP_DIR);
    },
    filename: function (req, file, cb) {
        const extensao = path.extname(
            file.originalname || ""
        ).toLowerCase();

        const nomeBase = path.basename(
            file.originalname || "video",
            extensao
        )
            .replace(/[^a-zA-Z0-9_-]/g, "_")
            .slice(0, 80);

        const nomeFinal =
            Date.now() +
            "_" +
            nomeBase +
            extensao;

        cb(null, nomeFinal);
    }
});

const uploadVideoTemporario = multer({
    storage: storageVideoTemporario,
    limits: {
        fileSize: 100 * 1024 * 1024
    },
    fileFilter: function (req, file, cb) {
        if (
            file &&
            file.mimetype &&
            file.mimetype.startsWith("video/")
        ) {
            cb(null, true);
        } else {
            cb(
                new Error(
                    "Apenas arquivos de vídeo são permitidos."
                )
            );
        }
    }
});

app.post("/api/html/upload", uploadImagem.single("imagem"), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({
                ok: false,
                erro: "Nenhuma imagem foi enviada."
            });
        }

    const tokenStudio = obterTokenStudio(req);

        try {
            await registrarUsoStudio("uploads", tokenStudio);
        } catch (erroUso) {
            if (req.file?.path && fs.existsSync(req.file.path)) {
                fs.unlinkSync(req.file.path);
            }

            if (erroUso.codigo === "LIMITE_ATINGIDO") {
                return res.status(403).json({
                    ok: false,
                    erro: erroUso.message,
                    limite_atingido: true,
                    tipo: "uploads"
                });
            }

            throw erroUso;
        }

        const url = "/uploads/" + encodeURIComponent(req.file.filename);

        return res.json({
            ok: true,
            acao: "upload_imagem",
            arquivo: req.file.filename,
            url,
            tamanho: req.file.size,
            tipo: req.file.mimetype
        });
    } catch (erro) {
        return res.status(500).json({
            ok: false,
            erro: "Erro ao processar imagem.",
            detalhe: erro.message
        });
    }
});

app.post(
    "/api/video/upload",
    uploadVideoTemporario.single("video"),
    async (req, res) => {
        let caminhoTemporario = "";

        try {
            const autenticacao = obterAutenticacaoStudio(req);

            if (!autenticacao) {
                if (req.file?.path && fs.existsSync(req.file.path)) {
                    fs.unlinkSync(req.file.path);
                }

                return res.status(401).json({
                    ok: false,
                    erro: "Autorização do Studio inválida ou expirada."
                });
            }

            if (!req.file) {
                return res.status(400).json({
                    ok: false,
                    erro: "Nenhum vídeo foi enviado."
                });
            }

            caminhoTemporario = req.file.path;

            try {
                await registrarUsoStudio(
                    "uploads",
                    autenticacao.token
                );
            } catch (erroUso) {
                if (
                    caminhoTemporario &&
                    fs.existsSync(caminhoTemporario)
                ) {
                    fs.unlinkSync(caminhoTemporario);
                }

                if (erroUso.codigo === "LIMITE_ATINGIDO") {
                    return res.status(403).json({
                        ok: false,
                        erro: erroUso.message,
                        limite_atingido: true,
                        tipo: "uploads"
                    });
                }

                throw erroUso;
            }

            const resultadoCloudinary =
                await enviarVideoCloudinary(
                    caminhoTemporario
                );

            if (!resultadoCloudinary.ok) {
                if (
                    caminhoTemporario &&
                    fs.existsSync(caminhoTemporario)
                ) {
                    fs.unlinkSync(caminhoTemporario);
                }

                return res.status(
                    resultadoCloudinary.status || 502
                ).json({
                    ok: false,
                    erro: resultadoCloudinary.erro,
                    resposta:
                        resultadoCloudinary.resposta || {}
                });
            }

            const dadosCloudinary =
                resultadoCloudinary.dados || {};

            const videoId =
                Date.now().toString() +
                "_" +
                Math.random()
                    .toString(36)
                    .slice(2, 10);

            const dadosVideo = {
                id: videoId,
                uid: autenticacao.uid,
                nome:
                    String(
                        req.body?.nome ||
                        req.file.originalname ||
                        "Vídeo"
                    ).slice(0, 200),
                url:
                    dadosCloudinary.secure_url ||
                    dadosCloudinary.url ||
                    "",
                secure_url:
                    dadosCloudinary.secure_url || "",
                public_id:
                    dadosCloudinary.public_id || "",
                resource_type:
                    dadosCloudinary.resource_type ||
                    "video",
                format:
                    dadosCloudinary.format || "",
                bytes:
                    Number(dadosCloudinary.bytes || 0),
                duration:
                    Number(dadosCloudinary.duration || 0),
                width:
                    Number(dadosCloudinary.width || 0),
                height:
                    Number(dadosCloudinary.height || 0),
                criado_em:
                    new Date().toISOString()
            };

            if (!dadosVideo.url) {
                if (
                    caminhoTemporario &&
                    fs.existsSync(caminhoTemporario)
                ) {
                    fs.unlinkSync(caminhoTemporario);
                }

                return res.status(502).json({
                    ok: false,
                    erro:
                        "Cloudinary não retornou a URL do vídeo."
                });
            }

            const firebase =
                await salvarVideoFirebase(
                    autenticacao.uid,
                    videoId,
                    dadosVideo
                );

            if (!firebase.ok) {
                console.error(
                    "[NEXUS FIREBASE MEDIA] Vídeo enviado ao Cloudinary, mas não foi salvo no Firebase:",
                    firebase.erro
                );

                if (
                    caminhoTemporario &&
                    fs.existsSync(caminhoTemporario)
                ) {
                    fs.unlinkSync(caminhoTemporario);
                }

                return res.status(500).json({
                    ok: false,
                    erro:
                        "Vídeo enviado ao Cloudinary, mas não foi possível salvar seus dados no Firebase.",
                    detalhe: firebase.erro
                });
            }

            if (
                caminhoTemporario &&
                fs.existsSync(caminhoTemporario)
            ) {
                fs.unlinkSync(caminhoTemporario);
            }

            return res.json({
                ok: true,
                uid: autenticacao.uid,
                video: dadosVideo
            });
        } catch (erro) {
            if (
                caminhoTemporario &&
                fs.existsSync(caminhoTemporario)
            ) {
                try {
                    fs.unlinkSync(caminhoTemporario);
                } catch (_) {}
            }

            console.error(
                "[NEXUS VIDEO] Falha no upload:",
                erro.message
            );

            return res.status(500).json({
                ok: false,
                erro: "Erro ao processar o upload do vídeo.",
                detalhe: erro.message
            });
        }
    }
);

app.get("/api/video/listar", async (req, res) => {
    try {
        const autenticacao = obterAutenticacaoStudio(req);

        if (!autenticacao) {
            return res.status(401).json({
                ok: false,
                erro: "Autorização do Studio inválida ou expirada."
            });
        }

        const resultado = await listarVideosFirebase(
            autenticacao.uid
        );

        if (!resultado.ok) {
            return res.status(500).json({
                ok: false,
                erro: "Não foi possível carregar os vídeos.",
                detalhe: resultado.erro
            });
        }

        const dados = resultado.dados || {};

        const videos = Object.values(dados)
            .filter((video) => {
                return (
                    video &&
                    String(video.uid || "") ===
                        String(autenticacao.uid)
                );
            })
            .sort((a, b) => {
                return String(
                    b.criado_em || ""
                ).localeCompare(
                    String(a.criado_em || "")
                );
            });

        return res.json({
            ok: true,
            uid: autenticacao.uid,
            videos
        });
    } catch (erro) {
        console.error(
            "[NEXUS VIDEO] Falha ao listar vídeos:",
            erro.message
        );

        return res.status(500).json({
            ok: false,
            erro: "Erro ao carregar a biblioteca de vídeos.",
            detalhe: erro.message
        });
    }
});

app.delete("/api/video/excluir", async (req, res) => {
    try {
        const autenticacao = obterAutenticacaoStudio(req);

        if (!autenticacao) {
            return res.status(401).json({
                ok: false,
                erro: "Autorização do Studio inválida ou expirada."
            });
        }

        const videoId = String(
            req.body?.video_id ||
            req.query?.video_id ||
            ""
        ).trim();

        if (!videoId) {
            return res.status(400).json({
                ok: false,
                erro: "ID do vídeo não informado."
            });
        }

        const resultadoLista = await listarVideosFirebase(
            autenticacao.uid
        );

        if (!resultadoLista.ok) {
            return res.status(500).json({
                ok: false,
                erro: "Não foi possível verificar a propriedade do vídeo.",
                detalhe: resultadoLista.erro
            });
        }

        const dados = resultadoLista.dados || {};
        const video = dados[videoId];

        if (
            !video ||
            String(video.uid || "") !==
                String(autenticacao.uid)
        ) {
            return res.status(404).json({
                ok: false,
                erro: "Vídeo não encontrado na sua biblioteca."
            });
        }

        const publicId = String(
            video.public_id || ""
        ).trim();

        if (!publicId) {
            return res.status(500).json({
                ok: false,
                erro: "O vídeo não possui public_id do Cloudinary para exclusão segura."
            });
        }

        const resultadoCloudinary =
            await excluirVideoCloudinary(
                publicId
            );

        if (!resultadoCloudinary.ok) {
            console.error(
                "[NEXUS CLOUDINARY] Falha ao excluir vídeo:",
                resultadoCloudinary.erro
            );

            return res.status(
                resultadoCloudinary.status || 502
            ).json({
                ok: false,
                erro: "Não foi possível excluir o vídeo do Cloudinary.",
                detalhe: resultadoCloudinary.erro
            });
        }

        const resultadoExclusao =
            await excluirVideoFirebase(
                autenticacao.uid,
                videoId
            );

        if (!resultadoExclusao.ok) {
            return res.status(500).json({
                ok: false,
                erro: "Vídeo removido do Cloudinary, mas não foi possível remover seu registro do Firebase.",
                detalhe: resultadoExclusao.erro
            });
        }

        return res.json({
            ok: true,
            uid: autenticacao.uid,
            video_id: videoId,
            mensagem: "Vídeo removido da biblioteca com sucesso."
        });
    } catch (erro) {
        console.error(
            "[NEXUS VIDEO] Falha ao excluir vídeo:",
            erro.message
        );

        return res.status(500).json({
            ok: false,
            erro: "Erro ao excluir o vídeo.",
            detalhe: erro.message
        });
    }
});

app.get("/", (req, res) => {
    const tokenQuery = String(req.query?.nexus_token || "").trim();

    if (tokenQuery) {
        const payload = validarTokenStudio(tokenQuery);

        if (payload) {
            res.setHeader(
                "Set-Cookie",
                `${STUDIO_COOKIE}=${encodeURIComponent(tokenQuery)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${STUDIO_TOKEN_MAX_AGE}`
            );

            return res.redirect("/");
        }

        return res.status(401).send("Autorização do Studio inválida ou expirada.");
    }

    return res.sendFile(
        path.join(WORKSPACE, "html", "public", "html_studio.html")
    );
});

app.get("/api/html/editar", async (req, res) => {
    const autenticacao = obterAutenticacaoStudio(req);

    if (!autenticacao) {
        return res.status(401).json({
            ok: false,
            erro: "Autorização do Studio inválida ou expirada."
        });
    }

    const arquivoHTML = String(req.query.arquivo || "").trim();

    if (!arquivoHTML) {
        return res.status(400).json({
            ok: false,
            erro: "Arquivo não informado."
        });
    }

    const nomeSeguro = path.basename(arquivoHTML);

    const acessoPagina = obterPaginaDoUsuario(
        nomeSeguro,
        autenticacao
    );

    if (!acessoPagina.ok) {
        return res.status(acessoPagina.status).json({
            ok: false,
            erro: acessoPagina.erro,
            ...(acessoPagina.detalhe
                ? { detalhe: acessoPagina.detalhe }
                : {})
        });
    }

    const indexFile = path.join(GERADOS_DIR, "index.json");

    if (!fs.existsSync(indexFile)) {
        return res.status(404).json({
            ok: false,
            erro: "Índice HTML não encontrado."
        });
    }

    try {
        const dados = JSON.parse(
            fs.readFileSync(indexFile, "utf-8")
        );

        const pagina = (dados.paginas || []).find(
            item => item.arquivo === nomeSeguro
        );

        if (!pagina) {
            return res.status(404).json({
                ok: false,
                erro: "Página não encontrada."
            });
        }

        const ferramentaDados = path.join(
            PYTHON_DIR,
            "ferramentas",
            "nexus_html_dados.py"
        );

        /*
         * O video_url fica salvo no index.json.
         * Portanto, mesmo que a ferramenta Python antiga
         * não conheça vídeo, o Studio continuará recebendo
         * o endereço Cloudinary salvo anteriormente.
         */

        if (!fs.existsSync(ferramentaDados)) {
            return res.json({
                ok: true,
                acao: "editar",
                pagina: {
                    ...pagina,
                    preco: pagina.preco || "",
                    descricao: pagina.descricao || "",
                    imagem: pagina.imagem || "",
                    video_url: pagina.video_url || ""
                }
            });
        }

        const resultado = await new Promise((resolve) => {
            execFile(
                "python3",
                [ferramentaDados, nomeSeguro],
                {
                    cwd: WORKSPACE,
                    env: process.env,
                    timeout: 120000,
                    maxBuffer: 5 * 1024 * 1024
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
        });

        let dadosHTML = {};

        try {
            dadosHTML = JSON.parse(
                resultado.stdout.trim()
            );
        } catch {
            dadosHTML = {};
        }

        res.json({
            ok: true,
            acao: "editar",
            pagina: {
                ...pagina,
                preco: dadosHTML.preco || pagina.preco || "",
                descricao: dadosHTML.descricao || pagina.descricao || "",
                imagem: pagina.imagem || "",
                video_url: pagina.video_url || ""
            }
        });

    } catch (erro) {
        res.status(500).json({
            ok: false,
            erro: "Erro ao carregar página.",
            detalhe: erro.message
        });
    }
});

app.get("/api/html/listar", (req, res) => {
    const autenticacao = obterAutenticacaoStudio(req);

    if (!autenticacao) {
        return res.status(401).json({
            ok: false,
            erro: "Autorização do Studio inválida ou expirada."
        });
    }

    try {
        const indexFile = path.join(GERADOS_DIR, "index.json");
        if (!fs.existsSync(indexFile)) return res.json({ ok: true, paginas: [] });
        const indice = JSON.parse(fs.readFileSync(indexFile, "utf-8"));

        const paginas = (indice.paginas || []).filter(
            pagina => paginaPertenceAoUsuario(pagina, autenticacao)
        );

        res.json({ ok: true, paginas });
    } catch (e) { res.json({ ok: true, paginas: [] }); }
});

app.get("/api/htmls", (req, res) => {
    const autenticacao = obterAutenticacaoStudio(req);

    if (!autenticacao) {
        return res.status(401).json({
            ok: false,
            erro: "Autorização do Studio inválida ou expirada."
        });
    }

    try {
        const indexFile = path.join(GERADOS_DIR, "index.json");
        if (!fs.existsSync(indexFile)) {
            return res.json([]);
        }

        const indice = JSON.parse(
            fs.readFileSync(indexFile, "utf-8")
        );

        const arquivosPermitidos = new Set(
            (indice.paginas || [])
                .filter(pagina =>
                    paginaPertenceAoUsuario(pagina, autenticacao)
                )
                .map(pagina => pagina.arquivo)
        );

        const files = fs.readdirSync(GERADOS_DIR)
            .filter(f =>
                f.endsWith(".html") &&
                arquivosPermitidos.has(f)
            )
            .sort()
            .reverse();

        res.json(files);
    } catch { res.json([]); }
});

app.post("/api/html/excluir", async (req, res) => {
    const autenticacao = obterAutenticacaoStudio(req);

    if (!autenticacao) {
        return res.status(401).json({
            ok: false,
            erro: "Autorização do Studio inválida ou expirada."
        });
    }

    const arquivoHTML = String(req.body?.arquivo || "").trim();
    if (!arquivoHTML) return res.status(400).json({ ok: false, erro: "Arquivo não informado." });
    const nomeSeguro = path.basename(arquivoHTML);

    const acessoPagina = obterPaginaDoUsuario(
        nomeSeguro,
        autenticacao
    );

    if (!acessoPagina.ok) {
        return res.status(acessoPagina.status).json({
            ok: false,
            erro: acessoPagina.erro,
            ...(acessoPagina.detalhe
                ? { detalhe: acessoPagina.detalhe }
                : {})
        });
    }

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

        // ----------------------------------------------------
        // EXCLUI TAMBÉM O HTML DO FIREBASE
        // ----------------------------------------------------

        let firebase = {
            ok: false,
            erro: "Exclusão Firebase não executada."
        };

        if (fs.existsSync(FIREBASE_SYNC_TOOL)) {
            firebase = await new Promise((resolve) => {
                execFile(
                    "python3",
                    [
                        FIREBASE_SYNC_TOOL,
                        "excluir",
                        nomeSeguro
                    ],
                    {
                        cwd: WORKSPACE,
                        env: process.env,
                        timeout: 120000,
                        maxBuffer: 5 * 1024 * 1024
                    },
                    (erroFirebase, stdoutFirebase, stderrFirebase) => {

                        if (erroFirebase) {
                            resolve({
                                ok: false,
                                erro: erroFirebase.message,
                                stdout: stdoutFirebase || "",
                                stderr: stderrFirebase || ""
                            });
                            return;
                        }

                        try {
                            resolve(
                                JSON.parse(
                                    (stdoutFirebase || "").trim()
                                )
                            );
                        } catch {
                            resolve({
                                ok: false,
                                erro: "O sincronizador Firebase não retornou JSON válido.",
                                stdout: stdoutFirebase || "",
                                stderr: stderrFirebase || ""
                            });
                        }
                    }
                );
            });
        }

        return res.json({
            ...dados,
            firebase
        });
    } catch {
        return res.status(500).json({ ok: false, erro: "A ferramenta de exclusão não retornou JSON válido.", stdout: resultado.stdout, stderr: resultado.stderr });
    }
});

app.post("/api/html/atualizar", async (req, res) => {
    const autenticacao = obterAutenticacaoStudio(req);

    if (!autenticacao) {
        return res.status(401).json({
            ok: false,
            erro: "Autorização do Studio inválida ou expirada."
        });
    }

    const arquivoHTML = String(req.body?.arquivo || "").trim();
    const titulo = String(req.body?.titulo || "").trim();
    const preco = String(req.body?.preco || "").trim();
    const descricao = String(req.body?.descricao || "").trim();
    const imagem = String(req.body?.imagem || "").trim();
    const video_url = String(req.body?.video_url || "").trim();

    if (video_url && !/^https:\/\/res\.cloudinary\.com\//i.test(video_url)) {
        return res.status(400).json({
            ok: false,
            erro: "Informe uma URL HTTPS válida de vídeo Cloudinary."
        });
    }

    if (!arquivoHTML) return res.status(400).json({ ok: false, erro: "Arquivo não informado." });
    const nomeSeguro = path.basename(arquivoHTML);

    const acessoPagina = obterPaginaDoUsuario(
        nomeSeguro,
        autenticacao
    );

    if (!acessoPagina.ok) {
        return res.status(acessoPagina.status).json({
            ok: false,
            erro: acessoPagina.erro,
            ...(acessoPagina.detalhe
                ? { detalhe: acessoPagina.detalhe }
                : {})
        });
    }

    const ferramentaDados = path.join(PYTHON_DIR, "ferramentas", "nexus_html_atualizar.py");
    if (!fs.existsSync(ferramentaDados)) {
        const indexFile = path.join(GERADOS_DIR, "index.json");
        if (fs.existsSync(indexFile)) {
            let indice = JSON.parse(fs.readFileSync(indexFile, "utf-8"));
            indice.paginas = (indice.paginas || []).map(p => p.arquivo === nomeSeguro ? {
                ...p,
                titulo,
                preco,
                descricao,
                imagem,
                video_url
            } : p);
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
            imagem,
            video_url
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

    try {
        const dados = JSON.parse(resultado.stdout.trim());

        if (!dados.ok) {
            return res.json(dados);
        }

        const firebase = await sincronizarHTMLFirebase(nomeSeguro);

        return res.json({
            ...dados,
            firebase: {
                sincronizado: firebase.ok,
                mensagem: firebase.mensagem || "",
                erro: firebase.ok ? "" : (firebase.erro || "")
            }
        });

    } catch {
        return res.status(500).json({
            ok: false,
            erro: "A ferramenta de atualização não retornou JSON válido.",
            stdout: resultado.stdout,
            stderr: resultado.stderr
        });
    }
});

// GERAR HTML COM GEMINI 3.1 LITE
app.post("/api/html/gerar", async (req, res) => {
    const nome = String(req.body?.nome || "").trim();
    const preco = String(req.body?.preco || "").trim();
    const descricao = String(req.body?.descricao || "").trim();
    const imagem = String(req.body?.imagem || "").trim();
    const video_url = String(req.body?.video_url || "").trim();

    if (video_url && !/^https:\/\/res\.cloudinary\.com\//i.test(video_url)) {
        return res.status(400).json({
            ok: false,
            erro: "Informe uma URL HTTPS válida de vídeo Cloudinary."
        });
    }

    if (!nome) return res.status(400).json({ ok: false, erro: "Nome do produto não informado." });
    if (!preco) return res.status(400).json({ ok: false, erro: "Preço não informado." });
    if (!descricao) return res.status(400).json({ ok: false, erro: "Descrição não informada." });

    let solicitacao = `Crie um anúncio HTML profissional para o produto "${nome}".\\nPreço: ${preco}\\nDescrição:\\n${descricao}\\n\\nREQUISITOS OBRIGATÓRIOS:\\n- Criar uma página HTML completa.\\n- Design moderno, profissional e responsivo.\\n- Criar uma área de imagem do produto.\\n- Criar botão "Comprar pelo WhatsApp".\\n- O botão "Comprar pelo WhatsApp" DEVE usar o compartilhamento padrão do WhatsApp, sem número de telefone fixo.\\n- Usar exatamente o formato https://wa.me/?text= seguido da mensagem codificada do produto.\\n- NUNCA inserir número de telefone de vendedor, administrador ou usuário no link do WhatsApp.\\n- NUNCA utilizar dados comerciais pessoais que não tenham sido fornecidos nesta solicitação.\\n- Criar botão "Compartilhar página".\\n- O botão Compartilhar deve usar a API nativa navigator.share quando disponível.\\n- Criar fallback de compartilhamento/cópia do endereço quando navigator.share não estiver disponível.\\n- Não utilizar GEMINI_API_KEY no HTML.\\n- Não colocar nenhuma chave de API no JavaScript do navegador.\\n`;
    if (imagem) solicitacao += `\nA imagem real do produto está disponível nesta URL:\n${imagem}\nUse essa URL como imagem principal do produto no HTML.\n`;

    if (video_url) {
        solicitacao += `\nO vídeo real do produto está disponível nesta URL Cloudinary:
${video_url}
Use exatamente essa URL como fonte de um elemento <video controls playsinline preload="metadata"> dentro de uma área de vídeo responsiva.
`;
    }

    const autenticacao = obterAutenticacaoStudio(req);

    if (!autenticacao) {
        return res.status(401).json({
            ok: false,
            erro: "Autorização do Studio inválida ou expirada."
        });
    }

    const tokenStudio = autenticacao.token;

    try {
        await registrarUsoStudio("geracoes", tokenStudio);
    } catch (erroUso) {
        if (erroUso.codigo === "LIMITE_ATINGIDO") {
            return res.status(403).json({
                ok: false,
                erro: erroUso.message,
                limite_atingido: true,
                tipo: "geracoes"
            });
        }

        return res.status(500).json({
            ok: false,
            erro: "Não foi possível registrar o uso da geração.",
            detalhe: erroUso.message
        });
    }

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
    indice.paginas.unshift({
        arquivo: nomeArquivo,
        titulo: nome,
        preco,
        descricao,
        imagem,
        video_url,
        uid: autenticacao.uid,
        criado_em: new Date().toISOString()
    });
    fs.writeFileSync(indexFile, JSON.stringify(indice, null, 2), "utf-8");
    // ========================================================
    // SINCRONIZAÇÃO AUTOMÁTICA COM FIREBASE
    // O HTML e o index.json já foram salvos antes desta etapa.
    // ========================================================

    const firebase = await sincronizarHTMLFirebase(nomeArquivo);

    return res.json({
        ok: true,
        arquivo: nomeArquivo,
        url: "/html_gerados/" + nomeArquivo,
        titulo: nome,
        firebase: {
            sincronizado: firebase.ok,
            mensagem: firebase.mensagem || "",
            erro: firebase.ok ? "" : (firebase.erro || "")
        }
    });
});

async function iniciarNexus() {
    console.log("");
    console.log("============================================");
    console.log("🚀 INICIANDO NEXUS HTML STUDIO");
    console.log("============================================");

    // --------------------------------------------------------
    // RESTAURAÇÃO AUTOMÁTICA DOS HTMLs DO FIREBASE
    // --------------------------------------------------------
    await restaurarHTMLsFirebase();

    // --------------------------------------------------------
    // INICIA O SERVIDOR SOMENTE APÓS A RESTAURAÇÃO
    // --------------------------------------------------------
    app.listen(PORT, "0.0.0.0", () => {
        console.log(`✅ NEXUS STUDIO gemini-3.1-flash-lite rodando http://127.0.0.1:${PORT}`);
        console.log(`WORKSPACE=${WORKSPACE}`);
        console.log(`PUBLIC=${PUBLIC_DIR}`);
        console.log(`GERADOS=${GERADOS_DIR}`);
        console.log(`UPLOADS=${UPLOADS_DIR}`);
        console.log("☁️ Firebase: restauração automática habilitada.");
        console.log("============================================");
    });
}

iniciarNexus().catch((erro) => {
    console.error("❌ Erro fatal ao iniciar o NEXUS:", erro);
    process.exit(1);
});
