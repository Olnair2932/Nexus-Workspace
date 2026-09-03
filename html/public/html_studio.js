(() => {
    "use strict";
    const $ = (id) => document.getElementById(id);
    const nome = $("produtoNome");
    const preco = $("produtoPreco");
    const descricao = $("produtoDescricao");
    const imagem = $("produtoImagem");
    const previewImagem = $("previewImagem");
    const previewTexto = $("previewTexto");
    const produtoPreviewImagem = $("produtoPreviewImagem");
    const produtoPreviewPlaceholder = $("produtoPreviewPlaceholder");
    const produtoPreviewNome = $("produtoPreviewNome");
    const produtoPreviewPreco = $("produtoPreviewPreco");
    const produtoPreviewDescricao = $("produtoPreviewDescricao");
    const btnGerar = $("btnGerar");
    const btnLimpar = $("btnLimpar");
    const listaHTML = $("listaHTML");

    const produtoExemplo = { nome: "Produto Exemplo Nexus", preco: "R$ 99,90", descricao: "Este é um produto de exemplo criado para testar o NEXUS HTML STUDIO." };

    function atualizarPreview() {
        produtoPreviewNome.textContent = nome.value.trim() || produtoExemplo.nome;
        produtoPreviewPreco.textContent = preco.value.trim() || produtoExemplo.preco;
        produtoPreviewDescricao.textContent = descricao.value.trim() || produtoExemplo.descricao;
    }

    imagem.addEventListener("change", function () {
        const arquivo = this.files && this.files[0];
        if (!arquivo) { previewImagem.style.display = "none"; produtoPreviewImagem.style.display = "none"; previewTexto.style.display = "block"; produtoPreviewPlaceholder.style.display = "flex"; return; }
        if (!arquivo.type.startsWith("image/")) { alert("Selecione um arquivo de imagem."); this.value = ""; return; }
        const leitor = new FileReader();
        leitor.onload = function (evento) {
            const imagemBase64 = evento.target.result;
            previewImagem.src = imagemBase64; previewImagem.style.display = "block"; previewTexto.style.display = "none";
            produtoPreviewImagem.src = imagemBase64; produtoPreviewImagem.style.display = "block"; produtoPreviewPlaceholder.style.display = "none";
        };
        leitor.onerror = function () { alert("Não foi possível carregar a imagem."); };
        leitor.readAsDataURL(arquivo);
    });

    nome.addEventListener("input", atualizarPreview);
    preco.addEventListener("input", atualizarPreview);
    descricao.addEventListener("input", atualizarPreview);

    btnLimpar.addEventListener("click", function () {
        nome.value = ""; preco.value = ""; descricao.value = ""; imagem.value = "";
        previewImagem.src = ""; previewImagem.style.display = "none"; previewTexto.style.display = "block";
        produtoPreviewImagem.src = ""; produtoPreviewImagem.style.display = "none"; produtoPreviewPlaceholder.style.display = "flex";
        atualizarPreview();
    });

    btnGerar.addEventListener("click", async function () {
        const nomeAtual = nome.value.trim();
        const precoAtual = preco.value.trim();
        const descricaoAtual = descricao.value.trim();
        if (!nomeAtual) { alert("Digite o nome do produto."); nome.focus(); return; }
        if (!precoAtual) { alert("Digite o preço do produto."); preco.focus(); return; }
        if (!descricaoAtual) { alert("Digite a descrição do produto."); descricao.focus(); return; }
        const textoOriginal = btnGerar.textContent;
        btnGerar.disabled = true; btnGerar.textContent = "⏳ GERANDO COM GEMINI 3.1 LITE...";
        try {
            let imagemUrl = "";
            if (imagem && imagem.files && imagem.files.length > 0) {
                const arquivoImagem = imagem.files[0];
                if (!arquivoImagem.type.startsWith("image/")) throw new Error("Selecione um arquivo de imagem válido.");
                btnGerar.textContent = "🖼️ ENVIANDO IMAGEM...";
                const formulario = new FormData(); formulario.append("imagem", arquivoImagem);
                const respostaUpload = await fetch("/api/html/upload", { method: "POST", body: formulario });
                const dadosUpload = await respostaUpload.json();
                if (!respostaUpload.ok ||!dadosUpload.ok) throw new Error(dadosUpload.erro || "Não foi possível enviar a imagem.");
                imagemUrl = dadosUpload.url;
            }
            btnGerar.textContent = "🤖 GEMINI 3.1 LITE GERANDO...";
            const resposta = await fetch("/api/html/gerar", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nome: nomeAtual, preco: precoAtual, descricao: descricaoAtual, imagem: imagemUrl })
            });
            const dados = await resposta.json();
            if (!resposta.ok ||!dados.ok) throw new Error(dados.erro || "Gemini não conseguiu gerar o HTML.");
            btnGerar.textContent = "✅ HTML GERADO!";
            await carregarHTMLsGerados();
            const abrir = window.confirm("✅ HTML gerado com Gemini 3.1 lite!\n\nArquivo: " + dados.arquivo + "\n\nDeseja abrir a página agora?");
            if (abrir && dados.url) window.open(dados.url, "_blank");
        } catch (erro) {
            console.error("NEXUS HTML STUDIO — Gemini:", erro);
            alert("❌ Erro ao gerar HTML:\n\n" + (erro.message || "Erro desconhecido."));
            btnGerar.textContent = textoOriginal;
        } finally {
            btnGerar.disabled = false;
            if (btnGerar.textContent === "⏳ GERANDO COM GEMINI 3.1 LITE...") btnGerar.textContent = textoOriginal;
            setTimeout(()=>{ btnGerar.textContent = "🚀 GERAR HTML"; }, 2000);
        }
    });

    function mostrarEstadoInicial() {
        listaHTML.innerHTML = `<div class="empty-state"><div class="empty-icon">📄</div><strong>Nenhuma página criada</strong><span>As páginas geradas pelo Nexus aparecerão aqui.</span></div>`;
    }

    function iniciar() { atualizarPreview(); mostrarEstadoInicial(); console.log("NEXUS HTML STUDIO iniciado - gemini-3.1-flash-lite - ~/workspace"); }
    iniciar();
})();

function visualizarHTML(arquivo) { if (!arquivo) return; window.open("/html_gerados/" + encodeURIComponent(arquivo), "_blank"); }
function editarHTML(arquivo) { if (!arquivo) return; window.location.href = "html_studio.html?editar=" + encodeURIComponent(arquivo); }
async function excluirHTML(arquivo) {
    if (!arquivo) return;
    if (!window.confirm("Deseja realmente excluir este HTML?")) return;
    try {
        const resposta = await fetch("/api/html/excluir", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ arquivo }) });
        const dados = await resposta.json();
        if (!resposta.ok ||!dados.ok) throw new Error(dados.erro || "Não foi possível excluir o HTML.");
        alert("🗑️ HTML excluído com sucesso!"); carregarHTMLsGerados();
    } catch (erro) { console.error("NEXUS: erro ao excluir", erro); alert("❌ Erro ao excluir: " + erro.message); }
}
function renderizarHTMLs(paginas) {
    const lista = document.getElementById("listaHTML"); if (!lista) return;
    if (!paginas || paginas.length === 0) { lista.innerHTML = `<div class="empty-state"><div class="empty-icon">📄</div><strong>Nenhuma página criada</strong><span>As páginas geradas pelo Nexus aparecerão aqui.</span></div>`; return; }
    lista.innerHTML = paginas.map((pagina) => {
        const arquivo = pagina.arquivo || ""; const titulo = pagina.titulo || arquivo;
        return `<div class="html-item"><div class="html-item-info"><strong>🛍️ ${titulo}</strong><small>${arquivo}</small></div><div class="html-item-acoes"><button type="button" onclick="visualizarHTML('${arquivo}')">👁️ Visualizar</button><button type="button" onclick="editarHTML('${arquivo}')">✏️ Editar</button><button type="button" onclick="excluirHTML('${arquivo}')">🗑️ Excluir</button></div></div>`;
    }).join("");
}
async function carregarHTMLsGerados() {
    try {
        const resposta = await fetch("/api/html/listar");
        if (!resposta.ok) throw new Error("Erro HTTP " + resposta.status);
        const dados = await resposta.json();
        if (!dados.ok) throw new Error(dados.erro || "Erro ao carregar páginas.");
        renderizarHTMLs(dados.paginas || []);
    } catch (erro) { console.error("NEXUS HTML STUDIO:", erro); }
}
document.addEventListener("DOMContentLoaded", carregarHTMLsGerados);

async function carregarModoEdicao() {
    const parametros = new URLSearchParams(window.location.search); const arquivo = parametros.get("editar"); if (!arquivo) return;
    try {
        const resposta = await fetch("/api/html/editar?arquivo=" + encodeURIComponent(arquivo));
        if (!resposta.ok) throw new Error("Erro HTTP " + resposta.status);
        const dados = await resposta.json();
        if (!dados.ok) throw new Error(dados.erro || "Não foi possível carregar o HTML.");
        const pagina = dados.pagina || {};
        const campoNome = document.getElementById("produtoNome"); if (campoNome) campoNome.value = pagina.titulo || "";
        const campoPreco = document.getElementById("produtoPreco"); if (campoPreco) campoPreco.value = pagina.preco || "";
        const campoDescricao = document.getElementById("produtoDescricao"); if (campoDescricao) campoDescricao.value = pagina.descricao || "";
        const btnSalvar = document.getElementById("btnSalvar"); if (btnSalvar) { btnSalvar.style.display = "inline-flex"; btnSalvar.onclick = salvarHTML; }
        console.log("NEXUS: modo edição carregado", pagina);
    } catch (erro) { console.error("NEXUS: erro ao carregar edição", erro); }
}
document.addEventListener("DOMContentLoaded", carregarModoEdicao);
if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", carregarModoEdicao, { once: true }); } else { carregarModoEdicao(); }

async function salvarHTML() {
    const parametros = new URLSearchParams(window.location.search);
    const arquivo = parametros.get("editar");

    if (!arquivo) {
        alert("Nenhuma página está em modo de edição.");
        return;
    }

    const titulo = document.getElementById("produtoNome")?.value.trim() || "";
    const preco = document.getElementById("produtoPreco")?.value.trim() || "";
    const descricao = document.getElementById("produtoDescricao")?.value.trim() || "";
    const campoImagem = document.getElementById("produtoImagem");
    const botao = document.getElementById("btnSalvar");

    if (!titulo) {
        alert("Informe o nome do produto.");
        return;
    }

    if (botao) {
        botao.disabled = true;
        botao.textContent = "⏳ SALVANDO...";
    }

    try {
        // ----------------------------------------------------
        // Recupera os dados atuais para preservar a imagem
        // caso nenhuma imagem nova seja selecionada.
        // ----------------------------------------------------
        let imagem = "";

        const respostaAtual = await fetch(
            "/api/html/editar?arquivo=" + encodeURIComponent(arquivo),
            { cache: "no-store" }
        );

        const textoAtual = await respostaAtual.text();

        let dadosAtuais = {};

        try {
            dadosAtuais = textoAtual ? JSON.parse(textoAtual) : {};
        } catch (e) {
            throw new Error(
                "O servidor não retornou JSON válido ao carregar os dados atuais."
            );
        }

        if (!respostaAtual.ok || !dadosAtuais.ok) {
            throw new Error(
                dadosAtuais.erro || "Não foi possível carregar os dados atuais."
            );
        }

        if (dadosAtuais.pagina) {
            imagem = dadosAtuais.pagina.imagem || "";
        }

        // ----------------------------------------------------
        // NOVA IMAGEM:
        // Converte o arquivo diretamente para Base64.
        // ----------------------------------------------------

        if (
            campoImagem &&
            campoImagem.files &&
            campoImagem.files.length > 0
        ) {
            const arquivoImagem = campoImagem.files[0];

            const LIMITE_IMAGEM = 15 * 1024 * 1024;

            if (
                !arquivoImagem.type ||
                !arquivoImagem.type.startsWith("image/")
            ) {
                throw new Error(
                    "Selecione um arquivo de imagem válido."
                );
            }

            if (arquivoImagem.size > LIMITE_IMAGEM) {
                const tamanhoMB = (
                    arquivoImagem.size / (1024 * 1024)
                ).toFixed(2);

                throw new Error(
                    "A imagem possui " +
                    tamanhoMB +
                    " MB. O limite máximo é de 15 MB por imagem."
                );
            }

            if (botao) {
                botao.textContent = "🖼️ CONVERTENDO IMAGEM...";
            }

            console.log("NEXUS: imagem selecionada:", {
                nome: arquivoImagem.name,
                tipo: arquivoImagem.type,
                tamanho: arquivoImagem.size,
                tamanhoMB: (
                    arquivoImagem.size / (1024 * 1024)
                ).toFixed(2)
            });

            imagem = await (async function () {
                /*
                 * NEXUS HTML STUDIO
                 * Leitura robusta de imagem no Android.
                 *
                 * Em vez de FileReader.readAsDataURL(), usamos
                 * URL.createObjectURL() + fetch() + ArrayBuffer.
                 * Isso evita falhas comuns ao selecionar imagens
                 * pela galeria/gerenciador de arquivos do Android.
                 */

                let objectUrl = "";

                try {
                    objectUrl = URL.createObjectURL(arquivoImagem);

                    console.log("NEXUS: lendo imagem via ObjectURL:", {
                        nome: arquivoImagem.name,
                        tipo: arquivoImagem.type,
                        tamanho: arquivoImagem.size
                    });

                    const respostaImagem = await fetch(objectUrl);

                    if (!respostaImagem.ok) {
                        throw new Error(
                            "Não foi possível acessar o arquivo de imagem."
                        );
                    }

                    const blob = await respostaImagem.blob();

                    if (!blob || !blob.size) {
                        throw new Error(
                            "A imagem selecionada está vazia ou não pôde ser lida."
                        );
                    }

                    const arrayBuffer = await blob.arrayBuffer();
                    const bytes = new Uint8Array(arrayBuffer);

                    /*
                     * Conversão Base64 em blocos.
                     * Evita estourar o limite de argumentos do
                     * String.fromCharCode() em imagens grandes.
                     */
                    let binario = "";
                    const TAMANHO_BLOCO = 8192;

                    for (
                        let i = 0;
                        i < bytes.length;
                        i += TAMANHO_BLOCO
                    ) {
                        const bloco = bytes.subarray(
                            i,
                            Math.min(i + TAMANHO_BLOCO, bytes.length)
                        );

                        binario += String.fromCharCode(...bloco);
                    }

                    const base64 = btoa(binario);

                    const mime =
                        blob.type ||
                        arquivoImagem.type ||
                        "application/octet-stream";

                    const resultado =
                        "data:" + mime + ";base64," + base64;

                    if (!resultado.startsWith("data:image/")) {
                        throw new Error(
                            "O arquivo selecionado não é uma imagem válida."
                        );
                    }

                    console.log(
                        "NEXUS: imagem convertida para Base64:",
                        resultado.length,
                        "caracteres"
                    );

                    return resultado;

                } catch (erro) {
                    console.error(
                        "NEXUS: falha ao ler imagem:",
                        erro
                    );

                    throw new Error(
                        "Não foi possível ler a imagem selecionada. " +
                        "Tente escolher a imagem novamente pela galeria."
                    );

                } finally {
                    if (objectUrl) {
                        URL.revokeObjectURL(objectUrl);
                    }
                }
            })();

            // O server.js aceita JSON de até 15 MB.
            // Base64 aumenta o tamanho aproximadamente 33%.
            if (imagem.length > 14000000) {
                throw new Error(
                    "A imagem é muito grande para ser enviada. " +
                    "Escolha uma imagem menor."
                );
            }
        }

        // ----------------------------------------------------
        // Salva HTML + dados + imagem Base64.
        // ----------------------------------------------------
        if (botao) {
            botao.textContent = "💾 SALVANDO DADOS...";
        }

        const resposta = await fetch("/api/html/atualizar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                arquivo,
                titulo,
                preco,
                descricao,
                imagem
            })
        });

        const textoResposta = await resposta.text();

        let dados = {};

        try {
            dados = textoResposta ? JSON.parse(textoResposta) : {};
        } catch (e) {
            console.error(
                "NEXUS: resposta não-JSON do servidor:",
                textoResposta
            );

            throw new Error(
                "O servidor não retornou JSON válido ao salvar."
            );
        }

        if (!resposta.ok || !dados.ok) {
            throw new Error(
                dados.erro || "Não foi possível salvar."
            );
        }

        alert("✅ Alterações salvas com sucesso!");

        if (botao) {
            botao.disabled = false;
            botao.textContent = "💾 SALVAR ALTERAÇÕES";
        }

        await carregarHTMLsGerados();

    } catch (erro) {
        console.error("NEXUS: erro ao salvar HTML", erro);

        alert(
            "❌ " +
            (erro.message || "Não foi possível salvar.")
        );

        if (botao) {
            botao.disabled = false;
            botao.textContent = "💾 SALVAR ALTERAÇÕES";
        }
    }
}
