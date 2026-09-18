"""Interface Web Moderna para o Servidor de Áudio Distribuído."""

HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Processador Distribuído de Áudio e Mídia</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #090e11;
            --bg-card: #121c21;
            --bg-card-hover: #17242a;
            --border: #223740;
            --text-main: #f0f6fc;
            --text-muted: #8b9eb0;
            --accent-green: #10b981;
            --accent-gold: #f59e0b;
            --accent-blue: #38bdf8;
            --accent-red: #ef4444;
            --radius-lg: 16px;
            --radius-md: 10px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px 16px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 28px;
            flex-wrap: wrap;
            gap: 16px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .logo-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--accent-green), var(--accent-gold));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 20px;
            color: #05100c;
        }

        .brand h1 {
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .brand p {
            font-size: 13px;
            color: var(--text-muted);
        }

        .system-status {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            background: rgba(16, 185, 129, 0.12);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .badge.degraded {
            background: rgba(245, 158, 11, 0.12);
            color: var(--accent-gold);
            border-color: rgba(245, 158, 11, 0.3);
        }

        .grid-layout {
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 24px;
        }

        @media (max-width: 900px) {
            .grid-layout {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 22px;
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .form-group {
            margin-bottom: 16px;
        }

        label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        input[type="file"], select, button {
            width: 100%;
            padding: 10px 14px;
            border-radius: var(--radius-md);
            background: #0b1317;
            border: 1px solid var(--border);
            color: var(--text-main);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        select:focus, input[type="file"]:focus {
            border-color: var(--accent-green);
        }

        .btn-primary {
            background: linear-gradient(135deg, #10b981, #059669);
            color: #ffffff;
            font-weight: 600;
            cursor: pointer;
            border: none;
            padding: 12px;
            border-radius: var(--radius-md);
            transition: opacity 0.2s, transform 0.1s;
        }

        .btn-primary:hover {
            opacity: 0.92;
        }

        .btn-primary:active {
            transform: scale(0.99);
        }

        .btn-sm {
            padding: 5px 10px;
            font-size: 12px;
            width: auto;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            border-radius: 6px;
            text-decoration: none;
        }

        .btn-outline {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-main);
        }

        .btn-outline:hover {
            background: var(--bg-card-hover);
            border-color: var(--text-muted);
        }

        .btn-danger {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: var(--accent-red);
        }

        .btn-danger:hover {
            background: rgba(239, 68, 68, 0.25);
        }

        .jobs-list {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .job-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 20px;
            transition: border-color 0.2s;
        }

        .job-card:hover {
            border-color: #335361;
        }

        .job-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
            gap: 12px;
            flex-wrap: wrap;
        }

        .job-info h3 {
            font-size: 15px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 4px;
        }

        .uuid-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text-muted);
            background: #091217;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid var(--border);
        }

        .status-pill {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-completed { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
        .status-processing { background: rgba(245, 158, 11, 0.15); color: var(--accent-gold); }
        .status-pending { background: rgba(56, 189, 248, 0.15); color: var(--accent-blue); }
        .status-failed { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }

        .waveform-container {
            background: #091217;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 10px;
            margin: 14px 0;
            text-align: center;
        }

        .waveform-img {
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            display: block;
            margin: 0 auto;
        }

        .audio-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin-top: 14px;
            background: #091217;
            padding: 12px;
            border-radius: var(--radius-md);
        }

        @media (max-width: 700px) {
            .audio-section { grid-template-columns: 1fr; }
        }

        .audio-player-box {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .audio-player-box span {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
        }

        audio {
            width: 100%;
            height: 34px;
            outline: none;
        }

        .meta-details {
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            margin-top: 12px;
            font-size: 12px;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            padding-top: 10px;
        }

        .checksum-box {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: #7dd3fc;
            background: #051016;
            padding: 4px 8px;
            border-radius: 6px;
            border: 1px solid #1a3342;
            word-break: break-all;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .tab-btn {
            padding: 8px 16px;
            border-radius: var(--radius-md);
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-muted);
            cursor: pointer;
            width: auto;
            font-weight: 600;
            font-size: 13px;
        }

        .tab-btn.active {
            background: var(--bg-card);
            border-color: var(--accent-green);
            color: var(--accent-green);
        }

        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8);
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
            z-index: 1000;
        }

        .modal-content {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            width: 100%;
            max-width: 650px;
            max-height: 80vh;
            overflow-y: auto;
            padding: 24px;
        }

        pre {
            background: #091217;
            padding: 14px;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #a7f3d0;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <div class="logo-icon">♬</div>
                <div>
                    <h1>Processador Distribuído de Áudio e Mídia</h1>
                    <p>Servidor FastAPI + FFmpeg + PostgreSQL + Subpastas UUID</p>
                </div>
            </div>
            <div class="system-status">
                <span id="healthBadge" class="badge" title="Verificando...">●</span>
                <a href="/docs" target="_blank" class="btn-sm btn-outline">Swagger API Docs ↗</a>
            </div>
        </header>

        <div class="grid-layout">
            <!-- Coluna de Envio -->
            <div>
                <div class="card">
                    <h2 class="card-title">Novo Processamento</h2>
                    <form id="uploadForm">
                        <div class="form-group">
                            <label for="mediaFile">Selecionar Arquivo de Áudio / Mídia</label>
                            <input type="file" id="mediaFile" name="media" required accept=".mp3,.wav,.ogg,.flac,.m4a,.mp4,.mkv,.avi,.mov,.webm">
                        </div>

                        <div class="form-group">
                            <label for="operationSelect">Operação Desejada</label>
                            <select id="operationSelect" name="operation" required>
                                <option value="normalize_volume">🔊 Normalização de Volume (EBU R128 loudnorm)</option>
                                <option value="convert_mp3">🎧 Converter para MP3 (190 kbps VBR)</option>
                                <option value="convert_wav">🎼 Converter para WAV (PCM 16-bit)</option>
                                <option value="extract_mp3">🎙️ Extrair Áudio de Vídeo (MP3)</option>
                                <option value="bass_boost">🎸 Realce de Graves (Bass Boost)</option>
                                <option value="speed_up">⚡ Acelerar Áudio (1.25x)</option>
                                <option value="slow_down">🐢 Desacelerar Áudio (0.85x)</option>
                                <option value="convert_mp4">🎬 Converter Vídeo para MP4</option>
                                <option value="compress_video">📦 Compactar Vídeo</option>
                            </select>
                        </div>

                        <button type="submit" id="submitBtn" class="btn-primary">Enviar para o Servidor</button>
                    </form>
                </div>

                <div class="card" style="margin-top: 20px;">
                    <h2 class="card-title">Estrutura de Armazenamento</h2>
                    <p style="font-size: 12px; color: var(--text-muted); line-height: 1.6;">
                        • <strong>Subpastas UUID:</strong> <code>storage/&lt;uuid&gt;/</code><br>
                        • <strong>Áudio Original:</strong> <code>original/audio.&lt;ext&gt;</code><br>
                        • <strong>Áudio Processado:</strong> <code>processed/audio.&lt;ext&gt;</code><br>
                        • <strong>Forma de Onda:</strong> <code>waveform.png</code><br>
                        • <strong>Metadados & Checksum:</strong> <code>meta.json</code><br>
                        • <strong>Lixeira:</strong> <code>storage/trash/&lt;uuid&gt;/</code>
                    </p>
                </div>
            </div>

            <!-- Coluna de Histórico / Lixeira -->
            <div>
                <div class="tabs">
                    <button class="tab-btn active" onclick="switchTab('active')">Processamentos Ativos</button>
                    <button class="tab-btn" onclick="switchTab('trash')">Lixeira (<span id="trashCount">0</span>)</button>
                </div>

                <div id="jobsContainer" class="jobs-list">
                    <p style="color: var(--text-muted); font-size: 14px;">Carregando processamentos...</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Meta.json -->
    <div id="metaModal" class="modal-overlay" onclick="closeModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 id="modalTitle" style="font-size: 16px;">Metadados (meta.json)</h3>
                <button onclick="closeModal()" class="btn-sm btn-outline" style="width: auto;">✕ Fechar</button>
            </div>
            <pre id="modalJsonContent"></pre>
        </div>
    </div>

    <script>
        let currentTab = 'active';

        async function updateHealth() {
            try {
                const res = await fetch('/api/health');
                const data = await res.json();
                const badge = document.getElementById('healthBadge');
                if (data.status === 'ok') {
                    badge.className = 'badge';
                    badge.innerHTML = '●';
                    badge.title = 'Servidor Online';
                } else {
                    badge.className = 'badge degraded';
                    badge.innerHTML = '●';
                    badge.title = `Servidor Degradado (${data.ffmpeg === 'ok' ? 'FFmpeg OK' : 'FFmpeg Ausente'})`;
                }
            } catch (err) {
                const badge = document.getElementById('healthBadge');
                badge.className = 'badge degraded';
                badge.innerHTML = '●';
                badge.title = 'Servidor Desconectado';
            }
        }

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.textContent.toLowerCase().includes(tab === 'active' ? 'ativos' : 'lixeira'));
            });
            loadJobs();
        }

        async function loadJobs() {
            try {
                const url = currentTab === 'trash' ? '/api/trash' : '/api/jobs';
                const res = await fetch(url);
                const jobs = await res.json();

                // update trash counter
                if (currentTab === 'active') {
                    fetch('/api/trash').then(r => r.json()).then(t => {
                        document.getElementById('trashCount').textContent = t.length;
                    }).catch(() => {});
                }

                const container = document.getElementById('jobsContainer');
                if (jobs.length === 0) {
                    container.innerHTML = `<div class="card" style="text-align: center; color: var(--text-muted); padding: 40px;">
                        ${currentTab === 'trash' ? 'A lixeira está vazia.' : 'Nenhum processamento registrado ainda. Envie um arquivo no formulário ao lado!'}
                    </div>`;
                    return;
                }

                container.innerHTML = jobs.map(job => {
                    const statusClass = `status-${job.status}`;
                    const statusText = {
                        pending: 'Aguardando',
                        processing: 'Processando',
                        completed: 'Concluído',
                        failed: 'Falhou'
                    }[job.status] || job.status;

                    const originalAudio = job.original_audio_url ? `
                        <div class="audio-player-box">
                            <span>Áudio Original</span>
                            <audio controls src="${job.original_audio_url}" preload="none"></audio>
                        </div>
                    ` : '';

                    const processedAudio = job.processed_audio_url ? `
                        <div class="audio-player-box">
                            <span>Áudio Processado (${job.operation})</span>
                            <audio controls src="${job.processed_audio_url}" preload="none"></audio>
                        </div>
                    ` : '';

                    const waveformHtml = job.processed_waveform_url ? `
                        <div class="waveform-container">
                            <span style="font-size: 11px; color: var(--text-muted); display: block; margin-bottom: 6px;">Forma de Onda (waveform.png)</span>
                            <img src="${job.processed_waveform_url}" class="waveform-img" alt="Forma de onda processada" />
                        </div>
                    ` : (job.original_waveform_url ? `
                        <div class="waveform-container">
                            <span style="font-size: 11px; color: var(--text-muted); display: block; margin-bottom: 6px;">Forma de Onda Original (waveform.png)</span>
                            <img src="${job.original_waveform_url}" class="waveform-img" alt="Forma de onda original" />
                        </div>
                    ` : '');

                    const actionsHtml = currentTab === 'trash' ? `
                        <button onclick="restoreJob('${job.id}')" class="btn-sm btn-outline">♻️ Restaurar</button>
                    ` : `
                        ${job.download_url ? `<a href="${job.download_url}" class="btn-sm btn-outline">⬇️ Baixar Resultado</a>` : ''}
                        <button onclick="viewMeta('${job.id}')" class="btn-sm btn-outline">📄 meta.json</button>
                        <button onclick="deleteJob('${job.id}')" class="btn-sm btn-danger">🗑️ Mover para Lixeira</button>
                    `;

                    return `
                        <div class="job-card">
                            <div class="job-header">
                                <div class="job-info">
                                    <h3>${job.original_name}</h3>
                                    <span class="uuid-tag">UUID: ${job.id}</span>
                                    <span style="font-size: 12px; color: var(--text-muted); margin-left: 8px;">Operação: <strong>${job.operation}</strong></span>
                                </div>
                                <div>
                                    <span class="status-pill ${statusClass}">${statusText}</span>
                                </div>
                            </div>

                            ${waveformHtml}

                            ${(originalAudio || processedAudio) ? `
                                <div class="audio-section">
                                    ${originalAudio}
                                    ${processedAudio}
                                </div>
                            ` : ''}

                            <div class="meta-details">
                                <div><strong>Tamanho:</strong> ${(job.file_size / 1024).toFixed(1)} KB</div>
                                <div><strong>Criado:</strong> ${new Date(job.created_at).toLocaleTimeString('pt-BR')}</div>
                                ${job.original_checksum ? `
                                    <div style="flex-basis: 100%;">
                                        <strong>Checksum SHA-256 (Original):</strong>
                                        <div class="checksum-box">${job.original_checksum}</div>
                                    </div>
                                ` : ''}
                                ${job.processed_checksum ? `
                                    <div style="flex-basis: 100%;">
                                        <strong>Checksum SHA-256 (Processado):</strong>
                                        <div class="checksum-box">${job.processed_checksum}</div>
                                    </div>
                                ` : ''}
                            </div>

                            <div style="display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap;">
                                ${actionsHtml}
                            </div>
                        </div>
                    `;
                }).join('');
            } catch (err) {
                console.error(err);
            }
        }

        async function deleteJob(id) {
            if (!confirm('Deseja mover este processamento para a lixeira (trash/)?')) return;
            try {
                await fetch(`/api/jobs/${id}`, { method: 'DELETE' });
                loadJobs();
            } catch (err) {
                alert('Erro ao mover para a lixeira.');
            }
        }

        async function restoreJob(id) {
            try {
                await fetch(`/api/trash/${id}/restore`, { method: 'POST' });
                loadJobs();
            } catch (err) {
                alert('Erro ao restaurar da lixeira.');
            }
        }

        async function viewMeta(id) {
            try {
                const res = await fetch(`/api/jobs/${id}/meta`);
                const data = await res.json();
                document.getElementById('modalTitle').textContent = `meta.json — ${id}`;
                document.getElementById('modalJsonContent').textContent = JSON.stringify(data, null, 2);
                document.getElementById('metaModal').style.display = 'flex';
            } catch (err) {
                alert('Erro ao carregar meta.json.');
            }
        }

        function closeModal(event) {
            document.getElementById('metaModal').style.display = 'none';
        }

        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            btn.textContent = 'Enviando e processando...';

            const formData = new FormData();
            formData.append('media', document.getElementById('mediaFile').files[0]);
            formData.append('operation', document.getElementById('operationSelect').value);

            try {
                const res = await fetch('/api/jobs', {
                    method: 'POST',
                    body: formData
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Erro ao criar processamento');
                }
                document.getElementById('uploadForm').reset();
                if (currentTab !== 'active') switchTab('active');
                else loadJobs();
            } catch (err) {
                alert('Falha: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Enviar para o Servidor';
            }
        });

        updateHealth();
        loadJobs();
        setInterval(() => {
            updateHealth();
            loadJobs();
        }, 3000);
    </script>
</body>
</html>
"""
