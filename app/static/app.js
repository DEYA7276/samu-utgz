/* SAMU · PWA y panel web: sin frameworks ni dependencias de CDN. */
'use strict';
const $=s=>document.querySelector(s);const $$=s=>[...document.querySelectorAll(s)];
const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const S={
  view:location.pathname==='/alumno'?'alumno':'inicio',
  user:null,
  csrf:'',
  step:0,
  draft:{},
  catalogs:null,
  signatures:{},
  students:[],
  selectedId:null,
  selectedReferral:null,
  rows:[],
  contacts:[],
  editContact:null,
  editInventory:null,
  referralTab:'new',
  referralDraft:null,
  bitacoraTab:'new',
  bitacoraDraft:null,
  editingFicheId:null,
  inventoryQuarter:undefined,
  inventoryFilter:'',
  importPreview:null,
  importFile:null,
  month:(()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`})(),
  dark:localStorage.getItem('samu-theme')==='dark',
  isOnline:navigator.onLine,
  syncPendingCount:0
};
const PROGRAMAS_UTGZ=['TSU en Administración, área Capital Humano','TSU en Administración, área Formulación y Evaluación de Proyectos','TSU en Agricultura Sustentable y Protegida','TSU en Contaduría','TSU en Energías Renovables','TSU en Gastronomía','TSU en Mantenimiento, área Industrial','TSU en Mecatrónica, área Automatización','TSU en Procesos Alimentarios','TSU en Tecnologías de la Información, área Desarrollo de Software Multiplataforma','TSU en Tecnologías de la Información, área Infraestructura de Redes Digitales','TSU en Turismo, área Hotelería','Ingeniería en Agricultura Sustentable y Protegida','Ingeniería en Energías Renovables','Ingeniería en Mantenimiento Industrial','Ingeniería en Mecatrónica','Ingeniería en Procesos Bioalimentarios','Ingeniería en Redes Inteligentes y Ciberseguridad','Ingeniería en Desarrollo y Gestión de Software','Licenciatura en Gestión del Capital Humano','Licenciatura en Innovación de Negocios y Mercadotecnia','Licenciatura en Gestión y Desarrollo Turístico'];
document.documentElement.dataset.theme=S.dark?'dark':'light';

function icon(name, size=18, cls=''){
  const c = cls ? ` class="${cls}"` : '';
  const s = size;
  const p = `width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"${c}`;
  switch(name){
    case 'dashboard':
    case 'home':
      return `<svg ${p}><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>`;
    case 'fichas':
      return `<svg ${p}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`;
    case 'importar':
    case 'users':
      return `<svg ${p}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`;
    case 'bitacora':
      return `<svg ${p}><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><line x1="12" y1="11" x2="12" y2="17"/><line x1="9" y1="14" x2="15" y2="14"/></svg>`;
    case 'canalizaciones':
      return `<svg ${p}><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;
    case 'inventario':
      return `<svg ${p}><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`;
    case 'contactos':
    case 'mail':
      return `<svg ${p}><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`;
    case 'logout':
      return `<svg ${p}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`;
    case 'download':
      return `<svg ${p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;
    case 'folder':
    case 'upload':
      return `<svg ${p}><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`;
    case 'alert-triangle':
    case 'warning':
      return `<svg ${p}><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
    case 'check-circle':
    case 'check':
      return `<svg ${p}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
    case 'info':
      return `<svg ${p}><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    case 'clipboard':
      return `<svg ${p}><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>`;
    case 'clock':
      return `<svg ${p}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`;
    case 'calendar':
      return `<svg ${p}><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`;
    case 'sun':
      return `<svg ${p}><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
    case 'moon':
      return `<svg ${p}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
    case 'google':
      return `<svg width="${s}" height="${s}" viewBox="0 0 24 24"><path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.03h3.88c2.27-2.09 3.665-5.17 3.665-9.12z"/><path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.03c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.13C3.27 21.44 7.35 24 12 24z"/><path fill="#FBBC05" d="M5.28 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.57H1.25C.45 8.16 0 9.98 0 12s.45 3.84 1.25 5.43l4.03-3.14z"/><path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.35 0 3.27 2.56 1.25 6.57l4.03 3.14c.95-2.83 3.6-4.96 6.72-4.96z"/></svg>`;
    default:
      return '';
  }
}

function themeToggle(){return `<button class="btn secondary sm theme-toggle" type="button" data-theme-toggle aria-pressed="${S.dark}">${S.dark?`${icon('sun',14)} Modo claro`:`${icon('moon',14)} Modo oscuro`}</button>`}
function setTheme(dark){S.dark=dark;document.documentElement.dataset.theme=dark?'dark':'light';localStorage.setItem('samu-theme',dark?'dark':'light');const meta=$('meta[name="theme-color"]');if(meta)meta.content=dark?'#183d30':'#28684f';$$('[data-theme-toggle]').forEach(b=>{b.innerHTML=dark?`${icon('sun',14)} Modo claro`:`${icon('moon',14)} Modo oscuro`;b.setAttribute('aria-pressed',String(dark))})}
const logo='/static/assets/samu-original.png';
const nowDate=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`};
const currentQuarter=()=>{const d=new Date(),m=d.getMonth();return `${['ENE-ABR','MAY-AGO','SEP-DIC'][Math.floor(m/4)]} ${d.getFullYear()}`};
const nowTime=()=>new Date().toTimeString().slice(0,5);
function referralHeaderText(date=nowDate()){const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(date);if(!m)return '';return `Código: FOR-${m[1].slice(-2)}-${m[2]} · REV. 01 · Emisión: ${m[3]}/${m[2]}/${m[1].slice(-2)}`;}
const toast=(message,error=false)=>{let t=$('#toast');if(!t)return;t.textContent=message;t.className=error?'error':'';t.style.display='block';clearTimeout(toast.t);toast.t=setTimeout(()=>t.style.display='none',5200)};

/* === MOTOR OFFLINE & INDEXEDDB DE SAMU === */
const OfflineDB = {
  dbName: 'SAMU_OFFLINE_STORE',
  dbVersion: 1,
  db: null,
  async open(){
    if(this.db) return this.db;
    return new Promise((resolve, reject)=>{
      const req = indexedDB.open(this.dbName, this.dbVersion);
      req.onupgradeneeded = e => {
        const d = e.target.result;
        if(!d.objectStoreNames.contains('sync_queue')){
          d.createObjectStore('sync_queue', {keyPath: 'id', autoIncrement: true});
        }
        if(!d.objectStoreNames.contains('offline_cache')){
          d.createObjectStore('offline_cache', {keyPath: 'key'});
        }
      };
      req.onsuccess = e => { this.db = e.target.result; resolve(this.db); };
      req.onerror = e => reject(e.target.error);
    });
  },
  async addQueue(endpoint, method, payload, description){
    const db = await this.open();
    return new Promise((resolve, reject)=>{
      const tx = db.transaction('sync_queue', 'readwrite');
      const store = tx.objectStore('sync_queue');
      const item = {
        endpoint,
        method,
        payload,
        description,
        createdAt: new Date().toISOString()
      };
      const req = store.add(item);
      req.onsuccess = () => {
        updateSyncBadge();
        resolve(req.result);
      };
      req.onerror = () => reject(req.error);
    });
  },
  async getQueue(){
    const db = await this.open();
    return new Promise((resolve, reject)=>{
      const tx = db.transaction('sync_queue', 'readonly');
      const store = tx.objectStore('sync_queue');
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  },
  async removeQueue(id){
    const db = await this.open();
    return new Promise((resolve, reject)=>{
      const tx = db.transaction('sync_queue', 'readwrite');
      const store = tx.objectStore('sync_queue');
      const req = store.delete(id);
      req.onsuccess = () => {
        updateSyncBadge();
        resolve();
      };
      req.onerror = () => reject(req.error);
    });
  },
  async setCache(key, data){
    try {
      const db = await this.open();
      const tx = db.transaction('offline_cache', 'readwrite');
      tx.objectStore('offline_cache').put({key, data, updated: new Date().toISOString()});
    } catch {}
  },
  async getCache(key){
    try {
      const db = await this.open();
      return new Promise((resolve)=>{
        const tx = db.transaction('offline_cache', 'readonly');
        const req = tx.objectStore('offline_cache').get(key);
        req.onsuccess = () => resolve(req.result?.data ?? null);
        req.onerror = () => resolve(null);
      });
    } catch { return null; }
  }
};

async function updateSyncBadge(){
  try {
    const queue = await OfflineDB.getQueue();
    S.syncPendingCount = queue.length;
    renderOfflineStatus();
  } catch {}
}

function renderOfflineStatus(){
  const bar = $('#offline-bar');
  if(!bar) return;
  if(!navigator.onLine){
    bar.style.display = 'flex';
    bar.className = 'offline-banner';
    bar.innerHTML = `<span>Modo sin conexión a Internet (Offline). Las consultas y registros se guardan localmente.</span>${S.syncPendingCount>0?`<span class="sync-badge">${S.syncPendingCount} pendiente(s) por sincronizar</span>`:''}`;
  } else if(S.syncPendingCount > 0){
    bar.style.display = 'flex';
    bar.className = 'offline-banner online-syncing';
    bar.innerHTML = `<span>Conexión restablecida. Tienes <b>${S.syncPendingCount}</b> registro(s) pendiente(s) de sincronizar.</span><button type="button" id="btn-sync-now">Sincronizar ahora</button>`;
  } else {
    bar.style.display = 'none';
  }
}

async function syncPendingQueue(){
  if(!navigator.onLine) {
    toast('No hay conexión a Internet para sincronizar todavía.', true);
    return;
  }
  const queue = await OfflineDB.getQueue();
  if(!queue.length) return;
  const bar = $('#offline-bar');
  if(bar){
    bar.className = 'offline-banner online-syncing';
    bar.innerHTML = `<span>Sincronizando registros pendientes con el servidor (${queue.length} restantes)…</span>`;
  }
  let synced = 0;
  for(const item of queue){
    try {
      await api(item.endpoint, {method: item.method, data: item.payload});
      await OfflineDB.removeQueue(item.id);
      synced++;
    } catch (err) {
      console.warn('Error sincronizando item:', item, err);
      // Si fue error de duplicado o regla de negocio, lo quitamos para no atorar la cola
      if(err.message?.includes('ya está registrado') || err.message?.includes('inexistente')){
        await OfflineDB.removeQueue(item.id);
      }
    }
  }
  await updateSyncBadge();
  if(synced > 0){
    toast(`¡Sincronización completada! ${synced} registro(s) subido(s) al servidor con éxito.`);
    if(S.user && S.view !== 'inicio') await view(S.view);
  }
}

window.addEventListener('online', ()=>{
  S.isOnline = true;
  updateSyncBadge();
  toast('¡Conexión a Internet restablecida!');
  syncPendingQueue();
});
window.addEventListener('offline', ()=>{
  S.isOnline = false;
  renderOfflineStatus();
  toast('Sin conexión a Internet. Activando Modo Offline automático.', true);
});
async function api(path,{method='GET',data,headers={},body=null}={}){
 const opts={method,credentials:'same-origin',headers:{...headers}};
 if(data!==undefined){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(data)}
 else if(body!==null){opts.body=body}
 if(!['GET','HEAD'].includes(method)&&S.csrf)opts.headers['X-CSRF-Token']=S.csrf;
 let res;
 try{
   res=await fetch(path,opts);
 }catch(err){
   // Si falla la red en petición GET, intentar leer del cache offline
   if(['GET','HEAD'].includes(method)){
     const cached = await OfflineDB.getCache(path);
     if(cached !== null) {
       return cached;
     }
   }
   throw Error('No se pudo conectar al servidor. Modo sin conexión activo.');
 }
 const raw=await res.text();let json={};try{json=raw?JSON.parse(raw):{}}catch{json={detail:'El servidor no devolvió una respuesta válida.'}}
 if(!res.ok){if(res.status===401&&S.user){S.user=null;S.csrf='';view('login')}throw Error(typeof json.detail==='string'?json.detail:'Ocurrió un error en la solicitud.')}
 // Si es petición GET exitosa, guardar en cache offline para emergencias sin internet
 if(['GET','HEAD'].includes(method)){
   OfflineDB.setCache(path, json);
 }
 return json;
}
function field(name,label,type='text',opts={}){const val=S.draft[name]??opts.value??'';const {required=false,full=false,placeholder='',max=255,readonly=false}=opts;const base=`name="${escapeHtml(name)}" ${required?'required':''} ${readonly?'readonly':''} maxlength="${max}"`;
 if(type==='textarea')return `<label class="field ${full?'full':''}">${escapeHtml(label)}<textarea ${base} rows="3" placeholder="${escapeHtml(placeholder)}">${escapeHtml(val)}</textarea></label>`;
 if(type==='select')return `<label class="field ${full?'full':''}">${escapeHtml(label)}<select ${base}>${(opts.options||[]).map(v=>`<option value="${escapeHtml(v)}" ${v===val?'selected':''}>${escapeHtml(v||'Selecciona una opción')}</option>`).join('')}</select></label>`;
 return `<label class="field ${full?'full':''}">${escapeHtml(label)}<input ${base} type="${type}" value="${escapeHtml(val)}" placeholder="${escapeHtml(placeholder)}"></label>`;
}
function bare(name,label,type='text',opts={}){const val=opts.value??'';const req=opts.required!==false;const base=`name="${escapeHtml(name)}" ${req?'required':''} maxlength="${opts.max||255}"`;return `<label class="field ${opts.full?'full':''}">${escapeHtml(label)}${type==='textarea'?`<textarea ${base} rows="3">${escapeHtml(val)}</textarea>`:type==='select'?`<select ${base}>${(opts.options||[]).map(v=>`<option value="${escapeHtml(v)}" ${v===val?'selected':''}>${escapeHtml(v||'Selecciona una opción')}</option>`).join('')}</select>`:`<input ${base} type="${type}" ${opts.min!==undefined?`min="${opts.min}"`:''} ${opts.pattern?`pattern="${opts.pattern}" title="${escapeHtml(opts.title||'')}"`:''} value="${escapeHtml(val)}">`}</label>`}
function checks(name,options){const active=S.draft[name]||[];return `<div class="checks">${options.map(c=>`<label><input type="checkbox" name="${name}" value="${escapeHtml(c)}" ${active.includes(c)?'checked':''}>${escapeHtml(c)}</label>`).join('')}</div>`}
function checksWithSelected(name,options,selected=[]){return `<div class="checks">${options.map(c=>`<label><input type="checkbox" name="${name}" value="${escapeHtml(c)}" ${(selected||[]).includes(c)?'checked':''}>${escapeHtml(c)}</label>`).join('')}</div>`}
function sig(name,label){return `<label class="field full">${escapeHtml(label)}</label><div class="sig-box full" data-signature="${name}"><canvas width="900" height="200" role="img" aria-label="Área para firmar con dedo o mouse"></canvas><div class="sig-actions"><small>Firma aquí con el dedo, lápiz o mouse</small><button class="link-button" type="button" data-clear="${name}">Borrar firma</button></div></div>`}
function obj(form){const data={};for(const [k,v] of new FormData(form)){if(data[k]!==undefined){if(!Array.isArray(data[k]))data[k]=[data[k]];data[k].push(v)}else data[k]=v}return data}
function parseErr(e){toast(e.message||'Error inesperado',true)}
function frame(content,inner=false){if(inner)return `<header class="hero-header"><a href="/" class="brand" data-view="${S.user?'dashboard':'inicio'}"><img src="${logo}" alt="Samu"><span><strong>SAMU</strong><small>Atención Médica Universitaria</small></span></a><div class="header-actions">${themeToggle()}<button class="btn secondary sm" data-view="consultar_estado">Estado / Credencial QR</button><button class="btn secondary sm" data-view="alumno">Ficha médica</button>${S.user?`<button class="btn primary sm" data-view="dashboard">Panel Enfermería</button>`:`<button class="btn primary sm" data-view="login">Enfermería</button>`}</div></header>${content}`;return content}

/* === VISTAS DE ESTADO, CREDENCIAL DIGITAL Y ESCÁNER QR === */
function badgeEstadoFicha(estado){
  switch(estado){
    case 'pendiente_revision':
    case 'pendiente':
      return '<span class="pill pending">Pendiente de revisión</span>';
    case 'en_revision':
      return '<span class="pill" style="background:#e0f2fe;color:#0369a1">En revisión médica</span>';
    case 'requiere_correccion':
      return '<span class="pill warn">Requiere corrección</span>';
    case 'validada':
      return '<span class="pill" style="background:#dcfce7;color:#15803d">Validada</span>';
    default:
      return `<span class="pill">${escapeHtml(estado)}</span>`;
  }
}

function consultarEstadoView(){
  return frame(`
    <main class="student-container" style="max-width:700px;margin:30px auto;padding:0 15px">
      <div class="student-lead">
        <div>
          <span class="eyebrow">Portal Estudiantil · UTGZ</span>
          <h1>Estado de mi Ficha Médica</h1>
          <p class="muted">Consulta el avance de revisión de tu expediente clínico y obtén tu Credencial Digital SAMU.</p>
        </div>
        <img src="${logo}" alt="Samu">
      </div>

      <section class="paper" id="estado-check-card">
        <h2>Verificar identidad</h2>
        <p class="hint">Inicia sesión con tu cuenta Google institucional o verifica tu identidad mediante un código OTP enviado a tu correo registrado.</p>

        <div style="margin:16px 0 22px;padding:16px;border:1px solid var(--line);border-radius:14px;background:var(--paper)">
          <strong style="display:block;margin-bottom:8px;color:var(--navy)">Acceso rápido con Google</strong>
          <p class="hint" style="margin:0 0 12px">Si registraste tu ficha médica con tu correo de Google, accede directamente sin esperar código:</p>
          <button type="button" id="btn-google-login" class="btn-google">${icon('google',20)}<span>Continuar con Google (Estudiante)</span></button>
        </div>

        <div style="border-top:1px solid var(--line);padding-top:18px">
          <strong style="display:block;margin-bottom:8px;color:var(--navy)">O verificar con código por correo</strong>
          <form id="form-consulta-otp">
            <div class="form-grid" style="grid-template-columns:1fr">
              ${bare('correo_consulta','Correo electrónico institucional o de contacto','email',{placeholder:'tu_correo@utgz.edu.mx'})}
            </div>
            <div class="actions" style="margin-top:15px">
              <button type="button" class="btn primary" id="btn-pedir-otp-consulta">Enviar código a mi correo</button>
            </div>
          </form>
        </div>

        <form id="form-verificar-consulta" style="display:none;margin-top:24px;border-top:1px solid var(--line);padding-top:20px">
          <div class="form-grid" style="grid-template-columns:1fr">
            <label class="field">Código de 6 dígitos recibido
              <input type="text" id="input-codigo-consulta" maxlength="6" pattern="[0-9]{6}" placeholder="Ej. 123456" required>
            </label>
          </div>
          <div class="actions" style="margin-top:15px">
            <button type="submit" class="btn green" id="btn-validar-consulta">Consultar mi estado y Credencial</button>
            <button type="button" class="btn secondary" id="btn-cambiar-correo-consulta">Cambiar correo</button>
          </div>
        </form>
      </section>

      <div id="resultado-credencial-card" style="display:none"></div>
    </main>
  `, true);
}

function renderCredencialCard(data){
  const fechaActualizacion = data.status_updated ? new Date(data.status_updated).toLocaleString('es-MX', {dateStyle:'medium', timeStyle:'short'}) : 'Reciente';
  const obsHtml = (data.estado === 'requiere_correccion' && data.observaciones_correccion) ? `
    <div class="warning-banner" style="margin:16px 0;text-align:left">
      <strong>Observación de Enfermería:</strong><br>
      ${escapeHtml(data.observaciones_correccion)}
      <p class="hint" style="margin-top:6px">Por favor acude al consultorio de Enfermería o comunícate con el área médica para actualizar este campo.</p>
    </div>
  ` : '';

  const avisosHtml = (data.avisos||[]).map(av => `
    <div style="border-left:4px solid var(--sea);padding:10px 14px;margin-bottom:10px;background:var(--paper);border-radius:0 10px 10px 0;text-align:left">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong style="color:var(--navy);font-size:0.9rem">${escapeHtml(av.titulo)}</strong>
        <small style="color:var(--muted);font-size:0.75rem">${escapeHtml(av.fecha)}</small>
      </div>
      <p style="margin:4px 0 0;font-size:0.85rem;color:var(--navy2)">${escapeHtml(av.mensaje)}</p>
    </div>
  `).join('') || '<p class="hint">No hay avisos recientes.</p>';

  // Guardar datos en sesión temporal del cliente
  window.currentStudentSession = {
    student_id: data.student_id,
    session_token: data.session_token
  };

  return `
    <div class="filter-pills" style="justify-content:center;margin-bottom:18px">
      <button type="button" class="filter-pill active" id="tab-student-credencial">Credencial Digital QR</button>
      <button type="button" class="filter-pill" id="tab-student-avisos">Centro de Avisos (${(data.avisos||[]).length})</button>
      <button type="button" class="filter-pill" id="tab-student-contacto">Actualizar mis Datos</button>
    </div>

    <!-- Pestaña 1: Credencial Digital QR -->
    <div id="panel-student-credencial">
      <section class="paper" style="border:2px solid #28684f;border-radius:24px;overflow:hidden;box-shadow:0 12px 36px rgba(40,104,79,0.12);background:linear-gradient(180deg,#ffffff 0%,#f7faf8 100%)">
        <div style="background:var(--navy);color:#fff;padding:20px;display:flex;align-items:center;justify-content:space-between">
          <div style="display:flex;align-items:center;gap:12px">
            <img src="${logo}" style="width:48px;height:48px;background:#fff;border-radius:50%;padding:4px" alt="SAMU">
            <div>
              <h3 style="color:#fff;margin:0;font-size:1.15rem;letter-spacing:0.5px">CREDENCIAL DIGITAL SAMU</h3>
              <span style="font-size:0.75rem;color:#b4d2bf;text-transform:uppercase">Universidad Tecnológica de Gutiérrez Zamora</span>
            </div>
          </div>
          <div>
            ${badgeEstadoFicha(data.estado)}
          </div>
        </div>

        <div style="padding:28px 24px;text-align:center">
          <h2 style="font-size:1.45rem;color:var(--navy2);margin:0 0 6px">${escapeHtml(data.nombre_estudiante)}</h2>
          <p class="muted" style="margin:0 0 16px;font-size:0.92rem">
            Matrícula: <b>${escapeHtml(data.matricula)}</b> · Folio: <span style="font-family:monospace">${escapeHtml(data.folio)}</span>
          </p>
          <span class="chip" style="display:inline-block;margin-bottom:20px">${escapeHtml(data.programa_educativo)}</span>

          ${obsHtml}

          <div style="background:#fff;border:1.5px dashed var(--line);border-radius:18px;padding:20px;display:inline-block;margin:10px auto;box-shadow:0 4px 15px rgba(0,0,0,0.04)">
            <div id="qrcode-container" style="display:flex;justify-content:center;margin:0 auto"></div>
            <small style="display:block;margin-top:10px;color:var(--muted);font-size:0.75rem">Identificador seguro: ${escapeHtml(data.qr_token)}</small>
          </div>

          <p class="hint" style="max-width:440px;margin:18px auto 0;line-height:1.5">
            <b>Seguridad médica:</b> Este código QR no contiene diagnósticos, alergias ni datos clínicos. Presenta esta credencial en la pantalla de tu celular al acudir al consultorio para que Enfermería escanee y abra tu expediente al instante.
          </p>

          <div class="actions" style="margin-top:22px;justify-content:center">
            <button type="button" class="btn primary sm" onclick="window.print()">Imprimir o Guardar PDF</button>
            <button type="button" class="btn secondary sm" data-view="inicio">Volver al inicio</button>
          </div>

          <small style="display:block;margin-top:14px;color:var(--muted);font-size:0.72rem">Última actualización de estado: ${fechaActualizacion}</small>
        </div>
      </section>
    </div>

    <!-- Pestaña 2: Centro de Avisos -->
    <div id="panel-student-avisos" style="display:none">
      <section class="paper">
        <h2>Centro de Avisos del Estudiante</h2>
        <p class="hint">Notificaciones y cambios de estado generados por el área de Enfermería de la UTGZ.</p>
        <div style="margin-top:18px">
          ${avisosHtml}
        </div>
      </section>
    </div>

    <!-- Pestaña 3: Actualizar Datos de Contacto -->
    <div id="panel-student-contacto" style="display:none">
      <section class="paper">
        <h2>Actualización Segura de Datos de Contacto</h2>
        <p class="hint">Modifica tu teléfono de contacto y los datos de tu contacto de emergencia sin acudir a ventanilla.</p>
        
        <form id="form-actualizar-datos-estudiante">
          <div class="form-grid">
            <label class="field">Mi teléfono celular personal
              <input type="tel" name="telefono_personal" value="${escapeHtml(data.telefono_personal||'')}" placeholder="Ej. 7661234567">
            </label>
            <label class="field">Nombre del contacto o tutor de emergencia
              <input type="text" name="nombre_contacto_emergencia" value="${escapeHtml(data.nombre_contacto_emergencia||'')}" required>
            </label>
            <label class="field">Teléfono del contacto de emergencia
              <input type="tel" name="telefono_contacto_emergencia" value="${escapeHtml(data.telefono_contacto_emergencia||'')}" required>
            </label>
          </div>
          <div class="actions" style="margin-top:20px">
            <button type="submit" class="btn green sm">Guardar cambios de contacto</button>
          </div>
        </form>
      </section>
    </div>
  `;
}

/* Modal Escáner QR de Enfermería con Cámara */
let html5QrScannerStream = null;
let qrScanAnimFrame = null;

function renderQrScannerModal(){
  return `
    <div id="qr-scanner-modal" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(16,24,32,0.85);backdrop-filter:blur(6px);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px">
      <div style="background:#fff;border-radius:24px;max-width:520px;width:100%;overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,0.3)">
        <div style="background:var(--navy);color:#fff;padding:18px 22px;display:flex;align-items:center;justify-content:space-between">
          <div style="display:flex;align-items:center;gap:10px">
            <strong style="font-size:1.05rem">Escanear Credencial QR de Alumno</strong>
          </div>
          <button type="button" id="btn-close-scanner" style="background:transparent;border:0;color:#fff;font-size:1.5rem;cursor:pointer;line-height:1">&times;</button>
        </div>

        <div style="padding:22px">
          <div style="position:relative;background:#000;border-radius:16px;overflow:hidden;aspect-ratio:4/3;display:flex;align-items:center;justify-content:center">
            <video id="qr-video" playsinline style="width:100%;height:100%;object-fit:cover"></video>
            <canvas id="qr-canvas" style="display:none"></canvas>
            
            <div style="position:absolute;width:60%;height:60%;border:2px solid #56b280;border-radius:14px;box-shadow:0 0 0 9999px rgba(0,0,0,0.45);pointer-events:none">
              <div style="width:100%;height:2px;background:#56b280;animation:scanBeam 2s infinite ease-in-out"></div>
            </div>
            <div id="qr-scan-loading" style="position:absolute;color:#fff;font-size:0.85rem;background:rgba(0,0,0,0.6);padding:6px 14px;border-radius:20px">
              Iniciando cámara…
            </div>
          </div>

          <div style="margin-top:16px;border-top:1px solid var(--line);padding-top:14px">
            <label class="field" style="font-size:0.82rem">O buscar manualmente por código / folio / token:
              <div style="display:flex;gap:8px;margin-top:6px">
                <input type="text" id="manual-qr-token" placeholder="Ingresa folio o token del QR">
                <button type="button" class="btn primary sm" id="btn-manual-qr-search">Buscar</button>
              </div>
            </label>
          </div>
        </div>
      </div>
    </div>
  `;
}

async function startQrCamera(){
  const video = $('#qr-video');
  const canvas = $('#qr-canvas');
  const loading = $('#qr-scan-loading');
  if(!video || !canvas) return;

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }
    });
    html5QrScannerStream = stream;
    video.srcObject = stream;
    await video.play();
    if(loading) loading.style.display = 'none';

    const ctx = canvas.getContext('2d', { willReadFrequently: true });

    function tick(){
      if(video.readyState === video.HAVE_ENOUGH_DATA){
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        if(window.jsQR){
          const code = window.jsQR(imgData.data, imgData.width, imgData.height, {
            inversionAttempts: 'dontInvert'
          });
          if(code && code.data){
            stopQrCamera();
            $('#qr-scanner-modal')?.remove();
            processScannedToken(code.data);
            return;
          }
        }
      }
      qrScanAnimFrame = requestAnimationFrame(tick);
    }
    qrScanAnimFrame = requestAnimationFrame(tick);
  } catch (err) {
    if(loading) loading.textContent = 'No se pudo acceder a la cámara. Usa la búsqueda manual.';
    toast('No se pudo iniciar la cámara: ' + (err.message || 'Permiso denegado'), true);
  }
}

function stopQrCamera(){
  if(qrScanAnimFrame) cancelAnimationFrame(qrScanAnimFrame);
  if(html5QrScannerStream){
    html5QrScannerStream.getTracks().forEach(t => t.stop());
    html5QrScannerStream = null;
  }
}

async function processScannedToken(rawToken){
  const token = rawToken.trim();
  toast('Procesando código QR…');
  try {
    const res = await api(`/api/qr/scan/${encodeURIComponent(token)}`);
    if(res.ok && res.student){
      toast(`¡Estudiante localizado! ${res.student.nombre_aspirante}`);
      S.selectedId = res.student.id;
      $('#app').innerHTML = ficheDetail(res.student);
      window.scrollTo({top:0, behavior:'smooth'});
    }
  } catch (err) {
    toast(err.message || 'Código QR no reconocido o inexistente en SAMU.', true);
  }
}

// Portada sin chips innecesarios
function welcome(){
  const actionsHtml = S.user ? `
    <div class="actions">
      <button class="btn primary" data-view="dashboard">Ir al Dashboard de Enfermería</button>
      <button class="btn green" data-view="importar">${icon('importar',16)} Importar alumnos (Excel/CSV)</button>
      <button class="btn outline" data-view="fichas">Ver Fichas médicas</button>
    </div>
  ` : `
    <div class="actions">
      <button class="btn primary" data-view="alumno">Llenar mi ficha médica</button>
      <button class="btn green" data-view="consultar_estado">${icon('fichas',16)} Consultar mi Ficha / Credencial QR</button>
      <button class="btn outline" data-view="login">Acceso a enfermería</button>
    </div>
  `;
  return frame(`<main class="hero"><div class="hero-grid"><div class="hero-left"><span class="eyebrow">Universidad Tecnológica de Gutiérrez Zamora</span><h1>Tu salud,<br><em>nuestro compromiso.</em></h1><p class="hero-desc">SAMU facilita el registro de fichas médicas y el trabajo diario del servicio de Enfermería de la universidad, de forma segura y organizada.</p>${actionsHtml}</div><img class="hero-art" src="${logo}" alt="Samu, cocodrilo médico con estetoscopio"></div></main>`,true);
}

function login(){
  return frame(`
    <main class="hero">
      <div class="hero-grid">
        <div class="hero-left">
          <span class="eyebrow">Acceso autorizado · UTGZ</span>
          <h1>Bienvenido<br><em>a Enfermería.</em></h1>
          <p class="hero-desc">Expedientes clínicos, bitácora, canalizaciones e inventario en un solo lugar. Acceso exclusivo para el personal de salud de la universidad.</p>
          <img src="${logo}" class="hero-art" alt="Samu" style="max-width:280px;margin:18px 0">
        </div>
        <section class="login-card">
          <span class="eyebrow">Personal de Enfermería</span>
          <h2>Iniciar sesión</h2>
          <p class="muted" id="login-intro-text">Ingresa con tus credenciales de enfermería.</p>

          <div id="google-auth-container" style="display:none">
            <div style="margin:16px 0">
              <button type="button" class="btn-google" id="btn-google-login">
                ${icon('google', 20)}
                <span>Continuar con Google</span>
              </button>
            </div>

            <div class="login-divider">
              <span>o ingresar con contraseña</span>
            </div>
          </div>

          <form id="login-form" class="form-grid" style="grid-template-columns:1fr">
            ${bare('email','Correo electrónico de enfermería','email')}
            ${bare('password','Contraseña','password')}
            <button class="btn primary" type="submit">Iniciar sesión</button>
            <p class="hint" id="login-hint-text">Acceso exclusivo para el personal de salud autorizado de la UTGZ.</p>
          </form>

          <hr class="divider">
          <p class="muted">¿Eres estudiante?</p>
          <button class="btn green" data-view="alumno" type="button">Llenar mi ficha médica (sin cuenta)</button>
        </section>
      </div>
    </main>
  `, true);
}

const FAMILIARES=['DIABETES','CÁNCER','OBESIDAD','TUMORACIONES','EPILEPSIA','CARDIOPATÍAS','HIPERTENSIÓN ARTERIAL','TUBERCULOSIS','FIEBRE REUMÁTICA'];
const PERSONALES=['PALUDISMO','TOSFERINA','CRISIS CONVULSIVAS','HEPATITIS','POLIOMIELITIS','PARASITOSIS','ARTRITIS','ANOREXIA','ANSIEDAD','DEPRESIÓN','BULIMIA','SARAMPIÓN','OTITIS','ASMA','NEUMONÍA','TIFOIDEA','CARIES','VARICELA','CEFALEAS','REFLUJO','PAPERAS','CARDIOPATÍAS','HIPERTENSIÓN ARTERIAL'];
const STEPS=['Aspirante','Antecedentes familiares','Antecedentes personales','Alergias','Situación médica actual','Médico particular','Autorización y firmas','Revisar y enviar'];
function ageFromBirth(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s||''))return '';const dob=new Date(s+'T12:00:00');if(Number.isNaN(dob.getTime()))return '';const now=new Date();let age=now.getFullYear()-dob.getFullYear();if(now.getMonth()<dob.getMonth()||(now.getMonth()===dob.getMonth()&&now.getDate()<dob.getDate()))age--;return age>=0&&age<=120?age:''}
function updateAge(){const form=$('#student-form');if(!form?.elements.fecha_nacimiento)return;const age=ageFromBirth(form.elements.fecha_nacimiento.value);if(form.elements.edad_calculada)form.elements.edad_calculada.value=age===''?'':age+' años'}
function studentStep(){const i=S.step;let html='';
 if(i===0)html=`
   <h2>Datos del estudiante / aspirante</h2>
   <p class="hint">Ingresa tus datos de identificación. Si eres alumno de nuevo ingreso y aún no cuentas con matrícula asignada, déjala en blanco; Enfermería la completará posteriormente.</p>
   <div class="form-grid">
     ${field('nombre_aspirante','NOMBRE COMPLETO DEL ESTUDIANTE','text',{required:true,full:true,max:200,placeholder:'Apellidos y nombres completos'})}
     ${field('correo','CORREO ELECTRÓNICO (INSTITUCIONAL O PERSONAL)','email',{required:true,full:true,max:250,placeholder:'ejemplo@utgz.edu.mx o personal'})}
     ${field('matricula','MATRÍCULA INSTITUCIONAL (OPCIONAL SI ERES DE NUEVO INGRESO)','text',{required:false,full:true,max:40,placeholder:'Déjalo en blanco si aún no cuentas con matrícula'})}
     ${field('programa_educativo','CARRERA / PROGRAMA EDUCATIVO','select',{required:false,full:true,options:['',...PROGRAMAS_UTGZ]})}
     ${field('fecha_nacimiento','FECHA DE NACIMIENTO','date',{required:true,max:10})}
     ${field('edad_calculada','EDAD CALCULADA AUTOMÁTICAMENTE','text',{readonly:true})}
     ${field('sexo','SEXO / GÉNERO','select',{required:true,full:true,options:['','Hombre','Mujer','Otro','Prefiero no especificar']})}
     ${field('nss','NSS (11 dígitos, si cuentas con uno)','text',{full:true,max:11,placeholder:'Déjalo en blanco si no lo conoces'})}
     ${field('tipo_sangre','TIPO DE SANGRE','select',{required:true,options:['','A+','A-','B+','B-','AB+','AB-','O+','O-','No lo sé']})}
   </div>
   <p class="hint">Tu correo electrónico se verificará con un código temporal antes de guardar tu expediente para comprobar tu identidad.</p>`;
 if(i===1)html=`<h2>ANTECEDENTES FAMILIARES</h2><p class="hint">Marca únicamente los antecedentes que correspondan. Si no padeces ninguno, deja todo sin seleccionar y da clic en «Siguiente».</p>${checks('antecedentes_familiares',FAMILIARES)}`;
 if(i===2)html=`<h2>ANTECEDENTES PERSONALES</h2><p class="hint">Si no padeces ninguno, deja todo sin seleccionar y da clic en «Siguiente».</p>${checks('antecedentes_personales',PERSONALES)}<div class="form-grid">${field('otro_personal','OTRO (ESPECIFICAR)', 'text',{full:true,max:200})}${field('intervenciones_quirurgicas','INTERVENCIONES QUIRÚRGICAS (OPERACIONES/CIRUGÍAS)','textarea',{full:true})}${field('traumatismos','TRAUMATISMOS (FRACTURAS)','textarea',{full:true})}</div>`;
 if(i===3)html=`<h2>ALERGIAS</h2><p class="hint">Si no tienes alergias, escribe «N/A» en los campos y da clic en «Siguiente».</p><div class="form-grid">${field('alergia_medicamentos','MEDICAMENTOS')}${field('alergia_alimentos','ALIMENTOS')}${field('alergia_plantas','PLANTAS')}${field('alergia_ambientales','AMBIENTALES')}${field('alergia_otros','OTROS (ESPECIFICAR)','text',{full:true})}</div>`;
 if(i===4)html=`<h2>SITUACIÓN MÉDICA ACTUAL</h2><p class="hint">Si no tienes padecimientos, tratamientos ni medicamentos que reportar, escribe «N/A» y da clic en «Siguiente».</p><div class="form-grid">${field('padecimientos','PADECIMIENTOS','textarea',{full:true})}${field('tratamiento_medico','TRATAMIENTO MÉDICO','textarea',{full:true})}${field('control_preventivo','CONTROL PREVENTIVO','textarea',{full:true})}${field('medicamentos_no_administrar','MEDICAMENTOS QUE NO SE LE DEBEN ADMINISTRAR NI EN CASO DE EMERGENCIA','textarea',{full:true})}</div>`;
 if(i===5)html=`<h2>DATOS DEL MÉDICO PARTICULAR</h2><p class="hint">Si no cuentas con médico particular o no tienes estos datos, puedes dejar los campos en blanco y dar clic en «Siguiente».</p><div class="form-grid">${field('nombre_medico','NOMBRE DEL MÉDICO')}${field('telefono_medico','TELÉFONO DEL MÉDICO','tel')}${field('hospital_preferencia','HOSPITAL DE SU PREFERENCIA','text',{full:true})}</div>`;
 if(i===6)html=`<h2>AUTORIZACIÓN Y FIRMA</h2><p class="hint">Se registra la autorización expresa para el traslado al Seguro Social en caso de accidente o emergencia médica. Registra tus datos de contacto de emergencia y tu firma digital.</p><div class="form-grid">${field('nombre_padre_tutor','NOMBRE DEL PADRE DE FAMILIA, TUTOR O CONTACTO DE EMERGENCIA','text',{required:true})}${field('telefono_padre_tutor','TELÉFONO DE CONTACTO DE EMERGENCIA','tel',{required:true})}<label class="inline-check full"><input type="checkbox" name="autoriza_traslado" ${S.draft.autoriza_traslado?'checked':''} required> AUTORIZO EL TRASLADO AL SEGURO SOCIAL EN CASO DE ACCIDENTES</label>${sig('firma_aspirante','NOMBRE Y FIRMA DIGITAL DEL ESTUDIANTE / ASPIRANTE')}</div>`;
 if(i===7)html=`
   <h2>Revisar y enviar ficha médica</h2>
   <p class="muted">Confirma que tus datos sean correctos antes de enviarlos a Enfermería.</p>
   
   <div class="save-banner">
     <strong>${escapeHtml(S.draft.nombre_aspirante||'')}</strong><br>
     Matrícula: <b>${escapeHtml(S.draft.matricula||'Pendiente (Nuevo ingreso)')}</b> · 
     Correo: <b>${escapeHtml(S.draft.correo||'')}</b> · 
     ${escapeHtml(S.draft.fecha_nacimiento||'')} (${escapeHtml(ageFromBirth(S.draft.fecha_nacimiento))} años) · 
     Sexo: ${escapeHtml(S.draft.sexo||'')}
   </div>

    <div class="privacy-notice-box">
      <div class="privacy-icon">${icon('info', 22)}</div>
      <div class="privacy-body">
        <h4>Aviso de Privacidad · Aplicación SAMU UTGZ</h4>
        <p>
          El <strong>Sistema de Atención Médica Universitaria (SAMU)</strong> de la UTGZ trata los datos de identificación, contacto y antecedentes de salud recabados con estricta confidencialidad y medidas técnicas de cifrado.
        </p>
        <details class="privacy-details">
          <summary>Ver términos de privacidad de la aplicación</summary>
          <div style="margin-top:8px;line-height:1.5">
            <p><strong>1. Finalidad:</strong> La información clínica y de contacto se utiliza exclusivamente para la apertura y consulta de tu expediente médico universitario, atención médica de primeros auxilios, canalización ante emergencias y seguimiento de salud por parte del personal de Enfermería de la UTGZ.</p>
            <p style="margin-top:6px"><strong>2. Confidencialidad y Seguridad:</strong> Tus datos médicos se almacenan de forma protegida en el servidor institucional. La aplicación SAMU no comparte ni transfiere información médica con terceros no autorizados.</p>
            <p style="margin-top:6px"><strong>3. Consentimiento:</strong> Al registrar tu ficha médica, confirmas la veracidad de los datos declarados y autorizas su resguardo en la plataforma SAMU para tu propia atención de salud en el campus.</p>
          </div>
        </details>
        <label class="inline-check" style="margin-top:12px">
          <input type="checkbox" name="acepto_aviso" id="acepto_aviso" required checked>
          <b>He leído y acepto el aviso de privacidad de la app SAMU, y confirmo la veracidad de los datos declarados en esta ficha.</b>
        </label>
      </div>
    </div>

   <div class="otp-verification-card">
     <h3>Verificación de correo electrónico</h3>
     <p class="hint">
       Para proteger tu información y verificar que tienes acceso a <b>${escapeHtml(S.draft.correo||'tu correo')}</b>, solicita un código de verificación temporal de 6 dígitos.
     </p>
     <div class="actions" style="margin: 12px 0 16px">
       <button type="button" class="btn secondary sm" id="btn-request-otp">
         ${icon('mail', 16)} Solicitar código de verificación por correo
       </button>
       <span id="otp-timer-msg" class="muted" style="align-self:center;font-size:0.85rem"></span>
     </div>

     <div class="form-grid" style="grid-template-columns:1fr;max-width:320px">
       <label class="field">Código de verificación (6 dígitos)
         <input name="codigo_verificacion" id="input-codigo-otp" type="text" maxlength="6" pattern="[0-9]{6}" placeholder="Ej. 123456" autocomplete="one-time-code" required value="${escapeHtml(S.draft.codigo_verificacion||'')}">
       </label>
     </div>
   </div>

   <div class="form-grid">
     <div style="position:absolute;left:-9999px" aria-hidden="true">
       <label>Sitio web<input name="sitio_web" tabindex="-1" autocomplete="off"></label>
     </div>
     <div class="actions full" style="margin-top:20px">
       <button class="btn primary" type="submit" id="btn-submit-ficha">
         ${icon('check-circle', 16)} Confirmar y enviar ficha médica
       </button>
     </div>
   </div>
   <p class="hint">Al enviar, tu ficha quedará registrada de forma segura en SAMU para que Enfermería proceda a su validación clínica.</p>`;
 return html;
}
function student(){return frame(`<div class="student-container"><div class="student-lead"><div><span class="eyebrow">Ficha médica · UTGZ</span><h1>Registro del aspirante</h1><p class="muted">Completa las secciones del formato original de Enfermería.</p></div><img src="${logo}" alt="Samu"></div><section class="paper"><div class="section-title"><div><span class="eyebrow">Paso ${S.step+1} de ${STEPS.length}</span><h2>${STEPS[S.step]}</h2></div><span class="pill">Guardado temporal en esta pantalla</span></div><div class="step-indicator">${STEPS.map((_,i)=>`<span class="${i<=S.step?'on':''}"></span>`).join('')}</div><form id="student-form">${studentStep()}<div class="form-footer"><button type="button" class="btn secondary" id="student-prev" ${S.step===0?'disabled':''}>Anterior</button>${S.step!==7?`<button type="submit" class="btn green">Siguiente</button>`:''}</div></form></section><p class="hint">Por privacidad, esta ficha no se guarda sin que confirmes el envío. No cierres la página durante el llenado.</p></div>`,true)}

function menu(){
 let entries=[
   ['dashboard','dashboard','Inicio'],
   ['alertas','alert-triangle','Centro de Alertas'],
   ['fichas','fichas','Fichas médicas'],
   ['importar','importar','Importar alumnos'],
   ['bitacora','bitacora','Bitácora'],
   ['canalizaciones','canalizaciones','Canalizaciones'],
   ['inventario','inventario','Inventario'],
   ['contactos','contactos','Correos guardados']
 ];
 return `<aside class="sidebar"><a class="brand" href="/enfermeria" data-view="dashboard"><img src="${logo}" alt="Samu"><span><strong>SAMU</strong><small>Enfermería UTGZ</small></span></a><nav class="side-menu">${entries.map(([id,iconName,label])=>`<button data-view="${id}" class="${S.view===id?'active':''}"><span class="nav-icon" aria-hidden="true">${icon(iconName,18)}</span>${label}</button>`).join('')}<button id="logout"><span class="nav-icon" aria-hidden="true">${icon('logout',18)}</span>Cerrar sesión</button></nav><div class="side-footer">Los expedientes requieren autenticación. Cierra sesión al terminar.</div></aside>`
}
function adminLayout(content,title,sub){
  const syncBtn = S.syncPendingCount > 0 ? `<button type="button" class="sync-badge" id="btn-sync-now" style="cursor:pointer" title="Sincronizar registros con el servidor">${S.syncPendingCount} pendiente(s)</button>` : '';
  return `<div class="shell">${menu()}<main class="workarea"><div class="topline"><div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(sub)}</p></div><div class="topline-actions">${syncBtn}${themeToggle()}<span class="user-pill">${escapeHtml(S.user?.name||'Enfermería')}</span></div></div>${content}</main></div>`
}
function table(headers,rows){return `<div class="table-wrap"><table class="data-table"><thead><tr>${headers.map(h=>`<th>${escapeHtml(h)}</th>`).join('')}</tr></thead><tbody>${rows.length?rows.join(''):`<tr><td colspan="${headers.length}"><div class="empty">No hay registros para mostrar.</div></td></tr>`}</tbody></table></div>`}

/* Alertas Médicas Estructuradas */
function medicalAlertsHtml(alerts){
  if(!alerts)return '';
  if(alerts.estado==='no_proporcionado'){
    return `<div class="med-alert-box info"><div class="med-alert-icon">${icon('info',22)}</div><div class="med-alert-body"><h4>Información médica no proporcionada</h4><p>${escapeHtml(alerts.mensaje)}</p></div></div>`;
  }
  if(alerts.estado==='sin_condiciones'){
    return `<div class="med-alert-box success"><div class="med-alert-icon">${icon('check-circle',22)}</div><div class="med-alert-body"><h4>Sin condiciones médicas declaradas</h4><p>${escapeHtml(alerts.mensaje)}</p></div></div>`;
  }
  return `<div class="med-alert-box ${alerts.critico?'danger':'warning'}"><div class="med-alert-icon">${alerts.critico?icon('alert-triangle',22):icon('clipboard',22)}</div><div class="med-alert-body"><h4>Alertas médicas del estudiante</h4><p>${escapeHtml(alerts.mensaje)}</p>${alerts.alergias?.length?`<div style="margin-top:8px"><b>Alergias declaradas:</b><div class="med-tags">${alerts.alergias.map(a=>`<span class="med-tag danger"><span class="status-dot danger"></span>${escapeHtml(a.tipo)}: ${escapeHtml(a.detalle)}</span>`).join('')}</div></div>`:''}${alerts.cronicos?.length?`<div style="margin-top:8px"><b>Antecedentes / Condiciones crónicas:</b><div class="med-tags">${alerts.cronicos.map(c=>`<span class="med-tag warning"><span class="status-dot warning"></span>${escapeHtml(c.tipo)}: ${escapeHtml(c.detalle)}</span>`).join('')}</div></div>`:''}${alerts.contraindicados?.length?`<div style="margin-top:8px"><b>Medicamentos que NO se le deben administrar:</b><div class="med-tags">${alerts.contraindicados.map(m=>`<span class="med-tag danger"><span class="status-dot danger"></span>NO ADMINISTRAR: ${escapeHtml(m)}</span>`).join('')}</div></div>`:''}</div></div>`;
}

/* Centro de Alertas de Enfermeria */
function alertasView(d){
  const inv = d.inventario_alertas || {agotados:0,stock_bajo:0,por_caducar:0,caducados:0,total_alertas:0};
  const fichasAlerta = d.fichas_recientes_revision || [];
  const pendientes = d.pendientes_revision || 0;
  const enRevision = d.en_revision || 0;
  const requiere = d.requiere_correccion || 0;

  function alertRow(prioridad, tipo, titulo, desc, boton, destino){
    const cls = prioridad==='alta'?'danger': prioridad==='media'?'warning':'info';
    const dot = prioridad==='alta'?'red': prioridad==='media'?'yellow':'green';
    return `<div style="display:flex;align-items:flex-start;gap:14px;padding:14px 18px;border-bottom:1px solid var(--line);background:#fff">
      <span class="status-dot ${dot}" style="margin-top:5px;flex-shrink:0"></span>
      <div style="flex:1">
        <strong style="font-size:0.95rem;color:var(--navy)">${escapeHtml(titulo)}</strong>
        <p style="margin:3px 0 0;font-size:0.85rem;color:var(--navy2)">${escapeHtml(desc)}</p>
      </div>
      <span class="chip ${cls}" style="white-space:nowrap;font-size:0.75rem">${escapeHtml(tipo)}</span>
      ${boton?`<button class="btn sm secondary" data-view="${destino}" style="flex-shrink:0">${escapeHtml(boton)}</button>`:''}
    </div>`;
  }

  let altasRows='', mediasRows='', bajasRows='';

  // Alta prioridad: agotados, caducados, fichas requieren correccion
  if(inv.agotados>0) altasRows+=alertRow('alta','Inventario',`${inv.agotados} medicamento(s) agotado(s)`,'Insumo con existencia en cero. Requiere reposicion inmediata.','Ver inventario','inventario');
  if(inv.caducados>0) altasRows+=alertRow('alta','Inventario',`${inv.caducados} insumo(s) caducado(s)`,'Productos fuera de fecha de uso. Deben retirarse del servicio.','Ver inventario','inventario');
  if(requiere>0) altasRows+=alertRow('alta','Fichas medicas',`${requiere} ficha(s) requieren correccion de datos`,'El estudiante fue notificado de que debe actualizar su informacion de contacto.','Revisar fichas','fichas');

  // Media prioridad: stock bajo, por caducar, pendientes revision
  if(inv.stock_bajo>0) mediasRows+=alertRow('media','Inventario',`${inv.stock_bajo} medicamento(s) con stock bajo`,'Existencias inferiores al minimo recomendado. Programar compra.','Ver inventario','inventario');
  if(inv.por_caducar>0) mediasRows+=alertRow('media','Inventario',`${inv.por_caducar} insumo(s) proximos a caducar (menos de 60 dias)`,'Revisar lote y fecha antes de administrar.','Ver inventario','inventario');
  if(pendientes>0) mediasRows+=alertRow('media','Fichas medicas',`${pendientes} ficha(s) pendientes de revision`,'Nuevas fichas medicas de alumnos esperando validacion de Enfermeria.','Revisar fichas','fichas');

  // Baja prioridad: en revision
  if(enRevision>0) bajasRows+=alertRow('baja','Fichas medicas',`${enRevision} ficha(s) en proceso de revision`,'Fichas en revision activa. Sin accion urgente requerida.','Revisar fichas','fichas');

  const totalAlertas = inv.total_alertas + pendientes + enRevision + requiere;

  const seccion = (titulo, rows, cls) => rows ? `
    <section class="paper" style="margin-top:14px">
      <div class="section-title" style="border-left:4px solid ${cls==='alta'?'var(--danger,#c0392b)':cls==='media'?'#e67e22':'var(--sea)'};padding-left:12px">
        <div>
          <h2 style="margin:0;font-size:1rem">${titulo}</h2>
        </div>
      </div>
      <div style="border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-top:10px">${rows}</div>
    </section>` : '';

  const noAlertas = !altasRows && !mediasRows && !bajasRows;

  return adminLayout(`
    <section class="paper">
      <div class="section-title">
        <div>
          <h2>Centro de Alertas Administrativas</h2>
          <p class="hint">Avisos agrupados por prioridad. ${totalAlertas>0?`${totalAlertas} alerta(s) activa(s).`:'Sin alertas activas en este momento.'}</p>
        </div>
        <div class="actions">
          <button class="btn sm secondary" data-view="inventario">Ver inventario</button>
          <button class="btn sm secondary" data-view="fichas">Ver fichas</button>
        </div>
      </div>
      ${noAlertas?`<div class="empty" style="padding:40px 0"><p>No hay alertas activas en este momento. El sistema esta en orden.</p></div>`:''}
    </section>
    ${seccion('Prioridad alta — Requieren atencion inmediata', altasRows, 'alta')}
    ${seccion('Prioridad media — Revisar a la brevedad', mediasRows, 'media')}
    ${seccion('Prioridad baja — Informativo', bajasRows, 'baja')}
    ${fichasAlerta.length>0?`
    <section class="paper" style="margin-top:14px">
      <div class="section-title">
        <div><h2>Fichas recientes con estado pendiente</h2><p class="hint">Alumnos registrados recientemente que esperan revision.</p></div>
        <button class="btn sm secondary" data-view="fichas">Ver todas</button>
      </div>
      ${table(['Folio','Estudiante','Matricula','Estado','Accion'],fichasAlerta.map(f=>`<tr><td><span style="font-family:monospace;font-weight:700">${escapeHtml(f.folio)}</span></td><td><b>${escapeHtml(f.nombre)}</b></td><td>${escapeHtml(f.matricula)}</td><td>${badgeEstadoFicha(f.estado)}</td><td><button class="btn sm secondary" data-ficha="${f.id}">Revisar</button></td></tr>`))}
    </section>`:``}
  `, 'Centro de Alertas', 'Alertas de inventario, fichas medicas y seguimiento administrativo');
}

/* Dashboard Inteligente de Enfermería */
function dashboard(d){
  const inv = d.inventario_alertas || {agotados:0, stock_bajo:0, por_caducar:0, caducados:0, total_alertas:0};
  const compPct = d.comparativa_mes_pct ?? 0;
  const compLabel = compPct > 0 ? `+${compPct}% vs mes anterior` : compPct < 0 ? `${compPct}% vs mes anterior` : 'Igual que el mes anterior';
  const stats = [
    ['Atenciones hoy', d.atenciones_hoy??0, true, ''],
    ['Esta semana', d.atenciones_semana??0, false, ''],
    ['Atenciones del mes', d.atenciones_mes??0, false, compLabel],
    ['Estudiantes atendidos', d.alumnos_atendidos_total??0, false, `${d.alumnos_atendidos_mes??0} este mes`],
    ['Pendientes de revisión', d.pendientes??0, (d.pendientes||0)>0, `${d.requiere_correccion??0} requieren corrección`],
    ['Canalizaciones pendientes', d.canalizaciones_pendientes??0, (d.canalizaciones_pendientes||0)>0, `${d.validadas??0} fichas validadas`]
  ];

  const maxGrafica = Math.max(1, ...(d.grafica_mensual||[]).map(g=>g.total));
  const chartHtml = (d.grafica_mensual||[]).map(g=>{
    const pct = Math.max(8, Math.round((g.total / maxGrafica) * 100));
    return `<div class="chart-col"><span class="chart-col-val">${g.total}</span><div class="chart-col-bar" style="height:${pct}%" title="${escapeHtml(g.label)}: ${g.total} atenciones"></div><span class="chart-col-lbl">${escapeHtml(g.label)}</span></div>`;
  }).join('');

  const topMotivos = d.top_motivos || [];
  const maxMotivo = Math.max(1, ...topMotivos.map(m=>m.total));
  const motivosHtml = topMotivos.length ? topMotivos.map(m => {
    const w = Math.max(10, Math.round((m.total / maxMotivo) * 100));
    return `<div style="margin-bottom:10px">
      <div style="display:flex;justify-content:space-between;font-size:0.84rem;margin-bottom:4px">
        <span style="color:var(--navy);font-weight:600">${escapeHtml(m.motivo)}</span>
        <span style="color:var(--muted);font-weight:700">${m.total}</span>
      </div>
      <div style="background:var(--paper);border-radius:8px;height:10px;overflow:hidden">
        <div style="width:${w}%;height:100%;background:var(--sea);border-radius:8px"></div>
      </div>
    </div>`;
  }).join('') : '<p class="hint">Aún no hay suficientes registros para calcular motivos frecuentes.</p>';

  const alertBanner = inv.total_alertas > 0 ? `
    <div class="med-alert-box ${inv.agotados>0||inv.caducados>0?'danger':'warning'}">
      <div class="med-alert-icon">${icon('alert-triangle',22)}</div>
      <div class="med-alert-body" style="flex:1">
        <h4>Alertas activas de existencias e inventario</h4>
        <p>Se detectaron insumos que requieren atención de Enfermería:</p>
        <div class="med-tags" style="margin-top:6px">
          ${inv.agotados>0?`<span class="med-tag danger"><span class="status-dot danger"></span>${inv.agotados} agotado(s)</span>`:''}
          ${inv.caducados>0?`<span class="med-tag danger"><span class="status-dot danger"></span>${inv.caducados} caducado(s)</span>`:''}
          ${inv.stock_bajo>0?`<span class="med-tag warning"><span class="status-dot warning"></span>${inv.stock_bajo} con stock bajo</span>`:''}
          ${inv.por_caducar>0?`<span class="med-tag warning"><span class="status-dot warning"></span>${inv.por_caducar} próximos a caducar (&lt;60 días)</span>`:''}
        </div>
      </div>
      <div class="actions" style="align-self:center">
        <button class="btn sm secondary" data-view="alertas">Centro de Alertas</button>
        <button class="btn sm outline" data-view="inventario">Ver inventario</button>
      </div>
    </div>` : '';

  const quickActions = `
    <div class="quick-grid">
      <div class="quick-card" id="btn-dashboard-scan-qr" style="border:2px solid var(--sea);background:var(--mint);cursor:pointer">
        <div class="quick-card-icon" style="background:#28684f;color:#fff">${icon('fichas',22)}</div>
        <div><strong style="color:var(--navy)">Escanear Credencial QR</strong><small>Abrir cámara y localizar expediente</small></div>
      </div>
      <div class="quick-card" data-view="bitacora" data-bitacora-tab="new">
        <div class="quick-card-icon">${icon('bitacora',22)}</div>
        <div><strong>Nueva atención</strong><small>Registrar en bitácora</small></div>
      </div>
      <div class="quick-card" data-view="fichas">
        <div class="quick-card-icon">${icon('fichas',22)}</div>
        <div><strong>Fichas médicas</strong><small>Revisar y gestionar estados</small></div>
      </div>
      <div class="quick-card" data-view="canalizaciones">
        <div class="quick-card-icon">${icon('canalizaciones',22)}</div>
        <div><strong>Canalización</strong><small>Emitir canalización externa</small></div>
      </div>
      <div class="quick-card" data-view="importar">
        <div class="quick-card-icon">${icon('importar',22)}</div>
        <div><strong>Importar alumnos</strong><small>Carga Excel o CSV</small></div>
      </div>
      <div class="quick-card" data-view="inventario">
        <div class="quick-card-icon">${icon('inventario',22)}</div>
        <div><strong>Inventario</strong><small>Medicamentos y material</small></div>
      </div>
    </div>`;

  const recentAtt = (d.ultimas_atenciones||[]).map(a=>`
    <tr>
      <td>${escapeHtml(a.fecha)}</td>
      <td>${escapeHtml(a.hora)}</td>
      <td><b>${escapeHtml(a.nombre)}</b></td>
      <td>${escapeHtml(a.matricula||'—')}</td>
      <td>${escapeHtml(a.motivo)}</td>
    </tr>`).join('');

  const fichasRevisionRows = (d.fichas_recientes_revision||[]).map(f=>`
    <tr>
      <td><span style="font-family:monospace;font-weight:700">${escapeHtml(f.folio)}</span></td>
      <td><b>${escapeHtml(f.nombre)}</b></td>
      <td>${escapeHtml(f.matricula)}</td>
      <td>${badgeEstadoFicha(f.estado)}</td>
      <td><button class="btn sm secondary" data-ficha="${f.id}">Revisar</button></td>
    </tr>`).join('');

  return adminLayout(`
    <div class="stats" style="grid-template-columns:repeat(6,minmax(0,1fr))">
      ${stats.map(([label, n, isAccent, sub])=>`
        <div class="stat ${isAccent?'accent':''}">
          <small>${label}</small>
          <b>${n}</b>
          ${sub?`<span style="display:block;font-size:0.72rem;color:var(--muted);margin-top:4px">${escapeHtml(sub)}</span>`:''}
        </div>`).join('')}
    </div>

    ${alertBanner}

    <section class="paper">
      <div class="section-title">
        <div>
          <h2>Panel Operativo de Enfermería</h2>
          <p class="hint">Acceso rápido a las funciones principales del consultorio universitario</p>
        </div>
      </div>
      ${quickActions}
    </section>

    <div style="display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:18px" class="dash-split">
      <section class="paper">
        <div class="section-title">
          <div>
            <h2>Fichas médicas en proceso de revisión</h2>
            <p class="hint">Alumnos que requieren validación o cambio de estado</p>
          </div>
          <button data-view="fichas" class="btn sm secondary">Ver todas las fichas</button>
        </div>
        ${table(['Folio','Estudiante','Matrícula','Estado','Acción'], fichasRevisionRows ? [fichasRevisionRows] : [])}
      </section>

      <section class="paper">
        <div class="section-title">
          <div>
            <h2>Últimas atenciones registradas</h2>
            <p class="hint">Consultas recientes en la bitácora médica</p>
          </div>
          <button data-view="bitacora" data-bitacora-tab="list" class="btn sm secondary">Ver bitácora</button>
        </div>
        ${table(['Fecha','Hora','Estudiante','Matrícula','Motivo'], recentAtt ? [recentAtt] : [])}
      </section>
    </div>

    <div style="display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:18px;margin-top:18px" class="dash-split">
      <section class="paper">
        <div class="section-title">
          <div>
            <h2>Atenciones médicas mensuales</h2>
            <p class="hint">Historial de consultas registradas en los últimos 6 meses</p>
          </div>
        </div>
        <div class="chart-bar-wrap">${chartHtml}</div>
      </section>

      <section class="paper">
        <div class="section-title">
          <div>
            <h2>Motivos de atención más frecuentes</h2>
            <p class="hint">Principales causas de consulta registradas</p>
          </div>
        </div>
        <div style="margin-top:10px">${motivosHtml}</div>
      </section>
    </div>
  `, 'Dashboard de Enfermería', 'Estadísticas en tiempo real, alertas y accesos rápidos');
}

function fichas(rows){
  return adminLayout(`
    <section class="paper">
      <div class="section-title">
        <div>
          <h2>Fichas médicas de estudiantes</h2>
          <p class="hint">Formularios clínicos y expedientes validados</p>
        </div>
        <div class="actions">
          <button type="button" id="btn-open-qr-scanner" class="btn primary sm">Escanear QR</button>
          <button data-view="importar" class="btn green sm">${icon('importar',16)} Importar alumnos (Excel/CSV)</button>
        </div>
      </div>
      <div class="searchline">
        <input id="fichas-q" placeholder="Buscar por nombre, folio, matrícula o QR">
        <select id="fichas-estado">
          <option value="">Todos los estados</option>
          <option value="pendiente_revision">Pendiente de revisión</option>
          <option value="en_revision">En revisión</option>
          <option value="requiere_correccion">Requiere corrección</option>
          <option value="validada">Validadas</option>
        </select>
        <button id="fichas-search" class="btn secondary">Buscar</button>
      </div>
      ${table(['Folio','Aspirante / Estudiante','Matrícula','Estado','Registro','Acciones'],rows.map(r=>`<tr><td>${escapeHtml(r.folio)}</td><td>${escapeHtml(r.nombre_aspirante)}</td><td>${escapeHtml(r.matricula||'—')}</td><td>${badgeEstadoFicha(r.estado)}</td><td>${escapeHtml((r.created||'').slice(0,10))}</td><td><div class="actions"><button class="btn sm secondary" data-ficha="${r.id}">Revisar</button><button class="btn sm green" data-editfiche="${r.id}">Editar</button></div></td></tr>`))}
    </section>
  `,'Fichas médicas','Expedientes clínicos y registro de alumnos');
}

function ficheDetail(a){
  const d=a.datos||{};
  const blocks=[
    ['FECHA DE NACIMIENTO',d.fecha_nacimiento],
    ['EDAD ACTUAL',a.edad_actual==null?'—':a.edad_actual+' años'],
    ['SEXO / GÉNERO',d.sexo],
    ['NSS',d.nss],
    ['TIPO DE SANGRE',d.tipo_sangre],
    ['CARRERA / PROGRAMA EDUCATIVO',d.programa_educativo],
    ['GRUPO',d.grupo],
    ['ANTECEDENTES FAMILIARES',(d.antecedentes_familiares||[]).join(', ')],
    ['ANTECEDENTES PERSONALES',(d.antecedentes_personales||[]).join(', ')],
    ['OTRO (ESPECIFICAR)',d.otro_personal],
    ['INTERVENCIONES QUIRÚRGICAS',d.intervenciones_quirurgicas],
    ['TRAUMATISMOS',d.traumatismos],
    ['ALERGIAS / MEDICAMENTOS',d.alergia_medicamentos],
    ['ALERGIAS / ALIMENTOS',d.alergia_alimentos],
    ['ALERGIAS / PLANTAS',d.alergia_plantas],
    ['ALERGIAS / AMBIENTALES',d.alergia_ambientales],
    ['ALERGIAS / OTROS',d.alergia_otros],
    ['PADECIMIENTOS',d.padecimientos],
    ['TRATAMIENTO MÉDICO',d.tratamiento_medico],
    ['CONTROL PREVENTIVO',d.control_preventivo],
    ['MEDICAMENTOS QUE NO SE LE DEBEN ADMINISTRAR',d.medicamentos_no_administrar],
    ['NOMBRE DEL MÉDICO',d.nombre_medico],
    ['TELÉFONO DEL MÉDICO',d.telefono_medico],
    ['HOSPITAL DE SU PREFERENCIA',d.hospital_preferencia],
    ['AUTORIZA TRASLADO',d.autoriza_traslado?'SÍ':'NO'],
    ['NOMBRE DEL PADRE/TUTOR',d.nombre_padre_tutor],
    ['TELÉFONO DEL PADRE/TUTOR',d.telefono_padre_tutor]
  ];

  return adminLayout(`
    <section class="paper">
      <div class="section-title">
        <div>
          <h2>${escapeHtml(a.nombre_aspirante)} · ${escapeHtml(a.folio)}</h2>
          <p class="hint">Estado: ${escapeHtml(a.estado)} · Matrícula: ${escapeHtml(a.matricula||'Pendiente')} · Correo: ${escapeHtml(a.email_verificacion||'Pendiente')}</p>
        </div>
        <div class="actions">
          <button data-view="fichas" class="btn secondary sm">Volver a fichas</button>
        </div>
      </div>

      ${medicalAlertsHtml(a.alertas_medicas)}

      ${d.pre_importado ? `
        <div class="save-banner">
          <b>Expediente importado pendiente de datos clínicos:</b> Este estudiante fue registrado institucionalmente. Puedes completar sus datos médicos, antecedentes, alergias y contactos haciendo clic en <b>«Editar / Completar datos»</b>.
        </div>
      ` : ''}

      <div class="actions" style="margin:14px 0">
        <button class="btn primary sm" data-editfiche="${a.id}">${icon('clipboard',16)} Editar / Completar datos</button>
        <button class="btn green sm" data-history="${a.id}">${icon('clock',16)} Ver historial de atenciones</button>
        <button class="btn outline sm" data-pdf="ficha" data-id="${a.id}">${icon('download',16)} Descargar ficha médica PDF</button>
      </div>

      <hr class="divider">
      <div class="form-grid">${blocks.map(([label,val])=>`<div><small class="eyebrow" style="letter-spacing:0;font-size:.68rem">${escapeHtml(label)}</small><div style="margin:6px 0 13px;white-space:pre-wrap">${escapeHtml(val||'—')}</div></div>`).join('')}</div>
      <hr class="divider">
      <div class="form-grid">
        ${a.foto?`<div><b>Fotografía validada</b><img style="display:block;max-width:170px;border-radius:12px;margin-top:10px" src="${a.foto}" alt="Fotografía del alumno"></div>`:''}
        ${d.firma_padre_tutor?`<div><b>Firma del padre/tutor</b><img style="display:block;max-width:210px;max-height:100px;margin-top:10px" src="${d.firma_padre_tutor}" alt="Firma capturada"></div>`:''}
        ${d.firma_aspirante?`<div><b>Firma del aspirante</b><img style="display:block;max-width:210px;max-height:100px;margin-top:10px" src="${d.firma_aspirante}" alt="Firma capturada"></div>`:''}
      </div>
    </section>

    <!-- GESTIÓN DE ESTADO DE LA FICHA POR ENFERMERÍA -->
    <section class="paper" style="border-left:5px solid #28684f">
      <div class="section-title">
        <div>
          <h2>Control de Revisión y Estado de la Ficha</h2>
          <p class="hint">Estado actual: ${badgeEstadoFicha(a.estado)} · Token QR: <code style="background:#eaf2ee;padding:3px 8px;border-radius:6px">${escapeHtml(a.qr_token||'—')}</code></p>
        </div>
        <div class="actions">
          <button type="button" class="btn secondary sm" id="btn-regenerar-qr" data-id="${a.id}">Regenerar Código QR</button>
        </div>
      </div>

      <form id="form-cambiar-estado" data-id="${a.id}">
        <div class="form-grid">
          <label class="field">Asignar nuevo estado
            <select name="estado" id="select-estado-ficha">
              <option value="pendiente_revision" ${['pendiente','pendiente_revision'].includes(a.estado)?'selected':''}>Pendiente de revisión</option>
              <option value="en_revision" ${a.estado==='en_revision'?'selected':''}>En revisión médica</option>
              <option value="requiere_correccion" ${a.estado==='requiere_correccion'?'selected':''}>Requiere corrección</option>
              <option value="validada" ${a.estado==='validada'?'selected':''}>Validada</option>
            </select>
          </label>
          <div id="box-observaciones-correccion" style="${a.estado==='requiere_correccion'?'':'display:none'}">
            <label class="field">Indicaciones para el estudiante (sin datos clínicos sensibles)
              <textarea name="observaciones_correccion" rows="2" placeholder="Ej. Favor de acudir al consultorio para actualizar contacto de emergencia">${escapeHtml(a.observaciones_correccion||'')}</textarea>
            </label>
          </div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button type="submit" class="btn primary sm">Actualizar Estado</button>
        </div>
      </form>
    </section>

    ${a.estado!=='validada'?`
      <section class="paper">
        <h2>Validar matrícula y fotografía del alumno</h2>
        <form id="validate-form" data-id="${a.id}">
          <div class="form-grid">
            ${bare('matricula','Matrícula asignada al alumno','text',{value:a.matricula||''})}
            ${bare('correo','Correo electrónico institucional','email',{value:a.email_verificacion||''})}
            <label class="field">Fotografía del alumno
              <input type="file" id="foto-alumno" accept="image/jpeg,image/png" capture="environment" style="display:block;margin-top:10px">
            </label>
          </div>
          <div class="actions" style="margin-top:18px"><button class="btn green">Guardar matrícula y validar</button></div>
        </form>
      </section>`:`
      <section class="paper">
        <h2>Actualizar correo institucional · Solo Enfermería</h2>
        <form id="student-email-form" data-id="${a.id}">
          <div class="form-grid">${bare('correo','Correo electrónico del alumno','email',{value:a.email_verificacion||''})}</div>
          <div class="actions" style="margin-top:15px"><button class="btn green">Guardar correo</button></div>
        </form>
      </section>`}
  `,'Revisión de ficha médica','Información confidencial, solo para personal autorizado');
}

function ficheEdit(a){
  const d = a.datos || {};
  const fam = d.antecedentes_familiares || [];
  const pers = d.antecedentes_personales || [];

  return adminLayout(`
    <section class="paper">
      <div class="section-title">
        <div>
          <h2>Editar y completar expediente clínico</h2>
          <p class="hint">Estudiante: <b>${escapeHtml(a.nombre_aspirante)}</b> · Folio: <b>${escapeHtml(a.folio)}</b></p>
        </div>
        <div class="actions">
          <button type="button" class="btn secondary sm" data-cancel-edit="${a.id}">Volver sin guardar</button>
        </div>
      </div>

      <form id="edit-fiche-form" data-id="${a.id}">
        <h3 style="margin-top:16px;color:var(--navy)">1. Identificación y Datos Académicos</h3>
        <div class="form-grid">
          ${bare('nombre_aspirante','Nombre completo del alumno','text',{value:a.nombre_aspirante||'',required:true,full:true})}
          ${bare('matricula','Matrícula institucional','text',{value:a.matricula||'',required:false})}
          ${bare('correo','Correo electrónico institucional','email',{value:a.email_verificacion||'',required:false})}
          ${bare('programa_educativo','Carrera / Programa educativo','select',{value:d.programa_educativo||'',options:['',...PROGRAMAS_UTGZ],required:false})}
          ${bare('grupo','Grupo escolar','text',{value:d.grupo||'',required:false})}
          <label class="field">Actualizar fotografía del alumno
            <input type="file" id="foto-alumno-edit" accept="image/jpeg,image/png" style="display:block;margin-top:10px">
          </label>
          ${a.estado==='pendiente'?`
            <label class="inline-check full" style="margin-top:8px">
              <input type="checkbox" name="validar_ahora" ${a.matricula&&a.email_verificacion?'checked':''}>
              <b>Validar expediente</b> (Asigna estado "validada" para habilitar atención clínica completa).
            </label>
          `:''}
        </div>

        <h3 style="margin-top:24px;color:var(--navy)">2. Datos Generales y de Salud</h3>
        <div class="form-grid">
          ${bare('fecha_nacimiento','Fecha de nacimiento','date',{value:d.fecha_nacimiento||'',required:false})}
          ${bare('sexo','Sexo / Género','select',{value:d.sexo||'',options:['','Hombre','Mujer','Otro','Prefiero no especificar'],required:false})}
          ${bare('nss','NSS (11 dígitos)','text',{value:d.nss||'',max:11,required:false})}
          ${bare('tipo_sangre','Tipo de sangre','select',{value:d.tipo_sangre||'',options:['','A+','A-','B+','B-','AB+','AB-','O+','O-','No lo sé'],required:false})}
        </div>

        <h3 style="margin-top:24px;color:var(--navy)">3. Antecedentes Familiares</h3>
        <p class="hint">Selecciona los antecedentes médicos familiares declarados por el alumno.</p>
        ${checksWithSelected('antecedentes_familiares',FAMILIARES,fam)}

        <h3 style="margin-top:24px;color:var(--navy)">4. Antecedentes Personales Patológicos</h3>
        <p class="hint">Selecciona las enfermedades o antecedentes personales que apliquen.</p>
        ${checksWithSelected('antecedentes_personales',PERSONALES,pers)}
        <div class="form-grid" style="margin-top:12px">
          ${bare('otro_personal','Otro antecedente personal (especificar)','text',{value:d.otro_personal||'',full:true,required:false})}
          ${bare('intervenciones_quirurgicas','Intervenciones quirúrgicas (operaciones/cirugías)','textarea',{value:d.intervenciones_quirurgicas||'',full:true,required:false})}
          ${bare('traumatismos','Traumatismos (fracturas, lesiones previas)','textarea',{value:d.traumatismos||'',full:true,required:false})}
        </div>

        <h3 style="margin-top:24px;color:var(--navy)">5. Alergias</h3>
        <p class="hint">Registra alergias conocidas para alertar oportunamente al personal de guardia.</p>
        <div class="form-grid">
          ${bare('alergia_medicamentos','Alergia a medicamentos','text',{value:d.alergia_medicamentos||'',required:false})}
          ${bare('alergia_alimentos','Alergia a alimentos','text',{value:d.alergia_alimentos||'',required:false})}
          ${bare('alergia_plantas','Alergia a plantas','text',{value:d.alergia_plantas||'',required:false})}
          ${bare('alergia_ambientales','Alergia a factores ambientales','text',{value:d.alergia_ambientales||'',required:false})}
          ${bare('alergia_otros','Otras alergias (especificar)','text',{value:d.alergia_otros||'',full:true,required:false})}
        </div>

        <h3 style="margin-top:24px;color:var(--navy)">6. Situación Médica Actual</h3>
        <div class="form-grid">
          ${bare('padecimientos','Padecimientos crónicos o actuales','textarea',{value:d.padecimientos||'',full:true,required:false})}
          ${bare('tratamiento_medico','Tratamiento médico continuo','textarea',{value:d.tratamiento_medico||'',full:true,required:false})}
          ${bare('control_preventivo','Control preventivo','textarea',{value:d.control_preventivo||'',full:true,required:false})}
          ${bare('medicamentos_no_administrar','MEDICAMENTOS QUE NO SE LE DEBEN ADMINISTRAR','textarea',{value:d.medicamentos_no_administrar||'',full:true,required:false})}
        </div>

        <h3 style="margin-top:24px;color:var(--navy)">7. Médico Particular y Traslado en Emergencia</h3>
        <div class="form-grid">
          ${bare('nombre_medico','Nombre del médico particular','text',{value:d.nombre_medico||'',required:false})}
          ${bare('telefono_medico','Teléfono del médico','tel',{value:d.telefono_medico||'',required:false})}
          ${bare('hospital_preferencia','Hospital de su preferencia','text',{value:d.hospital_preferencia||'',full:true,required:false})}
          ${bare('nombre_padre_tutor','Nombre del padre de familia o tutor / emergencia','text',{value:d.nombre_padre_tutor||'',required:false})}
          ${bare('telefono_padre_tutor','Teléfono del tutor / emergencia','tel',{value:d.telefono_padre_tutor||'',required:false})}
          <label class="inline-check full" style="margin-top:8px">
            <input type="checkbox" name="autoriza_traslado" ${d.autoriza_traslado?'checked':''}>
            <b>AUTORIZO EL TRASLADO AL SEGURO SOCIAL EN CASO DE ACCIDENTES</b>
          </label>
        </div>

        <div class="actions" style="margin-top:28px">
          <button type="submit" class="btn green">${icon('check-circle',16)} Guardar cambios en el expediente</button>
          <button type="button" class="btn secondary" data-cancel-edit="${a.id}">Cancelar edición</button>
        </div>
      </form>
    </section>
  `, 'Completar expediente', 'Edición y actualización de datos clínicos del estudiante');
}

/* Historial Cronológico por Estudiante */
function renderHistory(h){
  const st = h.student;
  const items = h.items || [];
  return adminLayout(`
    <section class="paper">
      <div class="section-title">
        <div>
          <span class="eyebrow">Línea de tiempo médica</span>
          <h2>${escapeHtml(st.nombre)} · ${escapeHtml(st.matricula||st.folio)}</h2>
          <p class="hint">${escapeHtml(st.programa_educativo||'')} ${st.grupo?`· Grupo ${escapeHtml(st.grupo)}`:''}</p>
        </div>
        <div class="actions">
          <button class="btn sm secondary" data-ficha="${st.id}">Volver a la ficha</button>
        </div>
      </div>

      <div class="searchline" style="margin-top:14px">
        <input id="hist-periodo" type="month" placeholder="Filtrar por mes (AAAA-MM)">
        <button class="btn sm secondary" id="hist-filter-btn" data-studentid="${st.id}">Filtrar por mes</button>
        <button class="btn sm outline" id="hist-clear-btn" data-studentid="${st.id}">Ver todo el historial</button>
      </div>

      <div class="stats" style="grid-template-columns:repeat(3,1fr);margin:16px 0">
        <div class="stat"><small>Atenciones en bitácora</small><b>${h.total_atenciones}</b></div>
        <div class="stat"><small>Canalizaciones externas</small><b>${h.total_canalizaciones}</b></div>
        <div class="stat accent"><small>Total de eventos</small><b>${h.total_eventos}</b></div>
      </div>

      ${items.length ? `
        <div class="timeline">
          ${items.map(it => {
            const isRef = it.tipo === 'canalizacion';
            const det = it.detalles || {};
            return `
              <div class="timeline-item">
                <div class="timeline-dot ${isRef?'referral':''}"></div>
                <div class="timeline-card">
                  <div class="timeline-header">
                    <div>
                      <span class="pill ${isRef?'pending':''}">${isRef?'Canalización Externa':'Atención en Enfermería'}</span>
                      <h4 style="margin-top:6px">${escapeHtml(it.motivo)}</h4>
                    </div>
                    <span class="timeline-date">${icon('calendar',14)} ${escapeHtml(it.fecha)} · ${icon('clock',14)} ${escapeHtml(it.hora||'—')}</span>
                  </div>

                  <div class="timeline-tags">
                    ${!isRef ? `
                      ${det.toma_ta?`<span class="pill">T/A: ${escapeHtml(det.toma_ta)}</span>`:''}
                      ${det.suministro_medicamento && det.suministro_medicamento!='N/A'?`<span class="pill">Medicamento: ${escapeHtml(det.suministro_medicamento)}</span>`:''}
                      ${det.material_curacion && det.material_curacion!='N/A'?`<span class="pill">Material: ${escapeHtml(det.material_curacion)}</span>`:''}
                      ${det.otro_procedimiento && det.otro_procedimiento!='N/A'?`<div style="font-size:.85rem;color:var(--muted);width:100%;margin-top:6px"><b>Procedimiento:</b> ${escapeHtml(det.otro_procedimiento)}</div>`:''}
                    ` : `
                      ${det.ta?`<span class="pill">T/A: ${escapeHtml(det.ta)}</span>`:''}
                      ${det.fc?`<span class="pill">FC: ${escapeHtml(det.fc)}</span>`:''}
                      ${det.sato2?`<span class="pill">SatO2: ${escapeHtml(det.sato2)}</span>`:''}
                      ${det.temperatura?`<span class="pill">Tª: ${escapeHtml(det.temperatura)}</span>`:''}
                      ${det.elaboro?`<div style="font-size:.82rem;color:var(--muted);width:100%;margin-top:6px"><b>Elaboró:</b> ${escapeHtml(det.elaboro)}</div>`:''}
                      <button class="btn sm outline" data-pdf="canalizacion" data-id="${it.id}" style="margin-top:8px">Descargar PDF Canalización</button>
                    `}
                  </div>
                </div>
              </div>`;
          }).join('')}
        </div>
      ` : `<div class="empty">No se encontraron atenciones ni canalizaciones previas para este periodo.</div>`}
    </section>
  `, 'Historial de atenciones', 'Línea de tiempo cronológica y registro continuo');
}

/* Importación Masiva de Estudiantes */
function importarView(previewData = null){
  return adminLayout(`
    <section class="paper">
      <div class="section-title">
        <div>
          <h2>Importación masiva de estudiantes</h2>
          <p class="hint">Carga de listas institucionales desde archivos Excel (.xlsx) o CSV (.csv)</p>
        </div>
        <div class="actions">
          <a href="/api/estudiantes/plantilla?formato=xlsx" class="btn outline sm" download>${icon('download',16)} Descargar Plantilla Excel (.xlsx)</a>
          <a href="/api/estudiantes/plantilla?formato=csv" class="btn outline sm" download>${icon('download',16)} Descargar Plantilla CSV (.csv)</a>
        </div>
      </div>

      <div class="save-banner">
        <b>Procedimiento de importación:</b><br>
        1. Descarga la plantilla oficial en Excel o CSV.<br>
        2. Llena o exporta las columnas: <code>matricula</code>, <code>nombre_completo</code>, <code>carrera</code>, <code>grupo</code>, <code>correo</code>.<br>
        3. Selecciona tu archivo; el sistema generará una <b>vista previa automática</b> antes de aplicar cambios.<br>
        4. Las matrículas existentes se detectarán como duplicados y permitirán actualizar sus datos académicos sin alterar información médica previa.
      </div>

      <div class="dropzone" id="import-dropzone">
        <div class="dropzone-icon">${icon('folder',42)}</div>
        <h3 style="margin:0 0 4px">Selecciona o arrastra tu archivo Excel o CSV</h3>
        <p class="muted">Formatos aceptados: .xlsx, .xls, .csv (hasta 10 MB)</p>
        <input type="file" id="import-file" accept=".xlsx,.xls,.csv,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" style="display:none">
        <button type="button" class="btn secondary sm" id="btn-browse-file" style="margin-top:12px">Examinar archivo</button>
        <div id="file-chosen-name" style="margin-top:10px;font-weight:700;color:var(--navy)">${S.importFile?`Archivo: ${escapeHtml(S.importFile.name)}`:''}</div>
      </div>

      ${previewData ? `
        <div class="preview-results" style="margin-top:22px">
          <div class="stats" style="grid-template-columns:repeat(4,1fr);margin-bottom:16px">
            <div class="stat"><small>Total de filas</small><b>${previewData.total}</b></div>
            <div class="stat accent"><small>Nuevos a registrar</small><b>${previewData.nuevos_count}</b></div>
            <div class="stat"><small>Duplicados (actualizables)</small><b>${previewData.duplicados_count}</b></div>
            <div class="stat ${previewData.errores_count?'warn':''}"><small>Errores detectados</small><b>${previewData.errores_count}</b></div>
          </div>

          ${previewData.errores_count ? `
            <div class="med-alert-box danger" style="margin-bottom:16px">
              <div class="med-alert-icon">${icon('alert-triangle',22)}</div>
              <div class="med-alert-body">
                <h4>Filas con errores que serán omitidas (${previewData.errores_count})</h4>
                <ul style="margin:6px 0 0;padding-left:18px">
                  ${previewData.errores.map(err=>`<li>Fila ${err.fila}: Matrícula: ${escapeHtml(err.matricula||'Sin matrícula')} — ${escapeHtml(err.error)}</li>`).join('')}
                </ul>
              </div>
            </div>` : ''}

          <label class="inline-check full" style="margin:14px 0">
            <input type="checkbox" id="chk-update-dup" checked>
            <b>Actualizar datos académicos de estudiantes existentes</b> (carrera, grupo, nombre, correo). Conserva la información médica existente.
          </label>

          ${previewData.nuevos_count ? `
            <div style="margin-top:16px">
              <h3>Alumnos nuevos a registrar (${previewData.nuevos_count})</h3>
              ${table(['Fila','Matrícula','Nombre Completo','Carrera / Programa','Grupo','Correo'],
                previewData.nuevos.slice(0, 15).map(r=>`<tr><td>${r.fila}</td><td><b>${escapeHtml(r.matricula)}</b></td><td>${escapeHtml(r.nombre_completo)}</td><td>${escapeHtml(r.carrera)}</td><td>${escapeHtml(r.grupo)}</td><td>${escapeHtml(r.correo)}</td></tr>`))}
              ${previewData.nuevos.length > 15 ? `<p class="hint">Mostrando los primeros 15 registros de ${previewData.nuevos_count} alumnos nuevos.</p>` : ''}
            </div>` : ''}

          ${previewData.duplicados_count ? `
            <div style="margin-top:16px">
              <h3>Estudiantes existentes con matrícula coincidente (${previewData.duplicados_count})</h3>
              ${table(['Fila','Matrícula','Nombre en archivo','Carrera en archivo','Grupo en archivo'],
                previewData.duplicados.slice(0, 15).map(r=>`<tr><td>${r.fila}</td><td><b>${escapeHtml(r.matricula)}</b></td><td>${escapeHtml(r.nombre_archivo)}</td><td>${escapeHtml(r.carrera_archivo)}</td><td>${escapeHtml(r.grupo_archivo)}</td></tr>`))}
              ${previewData.duplicados.length > 15 ? `<p class="hint">Mostrando los primeros 15 registros de ${previewData.duplicados_count} duplicados.</p>` : ''}
            </div>` : ''}

          <div class="actions" style="margin-top:24px">
            <button type="button" class="btn green" id="btn-confirm-import">Confirmar e importar estudiantes</button>
            <button type="button" class="btn secondary" id="btn-cancel-import">Cancelar vista previa</button>
          </div>
        </div>
      ` : ''}
    </section>
  `, 'Importación masiva de estudiantes', 'Carga de listas escolares y actualización académica');
}

function studentDropdown(draft=null){
  return `<label class="field full">Vincular una ficha médica validada (opcional)<select name="student_id" id="pick-student"><option value="">Registro manual según formato</option>${S.students.map(a=>`<option value="${a.id}" ${String(draft?.student_id||'')===String(a.id)?'selected':''}>${escapeHtml(a.nombre)} · ${escapeHtml(a.matricula||'')}</option>`).join('')}</select></label><div id="picked-student-alerts"></div>`;
}

function bitacora(rows){
 const f=[['fecha','Fecha','date'],['hora','Hora','time'],['nombre','Nombre'],['matricula','Matrícula'],['edad','Edad','number'],['sexo','Sexo','select'],['programa_educativo','Programa educativo','select'],['grupo','Grupo'],['motivo_consulta','Motivo de consulta','textarea'],['toma_ta','Toma de T/A'],['otro_procedimiento','Otro procedimiento','textarea'],['suministro_medicamento','Suministro medicamento'],['material_curacion','Material de curación']];
 const form=`<section class="paper"><div class="section-title"><h2>Nueva atención del alumnado por el servicio de enfermería</h2></div><p class="hint">Formato FOR-23-04a · REV.01 · Emisión: 07/11/23</p><form id="bitacora-form"><div class="form-grid">${studentDropdown(S.bitacoraDraft)}${f.map(([k,l,t])=>bare(k,l,t||'text',{value:S.bitacoraDraft?.[k]??(k==='fecha'?nowDate():k==='hora'?nowTime():''),options:k==='sexo'?['',...['Hombre','Mujer','Otro','Prefiero no especificar']]:k==='programa_educativo'?['',...PROGRAMAS_UTGZ]:[],required:!['edad','sexo','programa_educativo','grupo','toma_ta','otro_procedimiento','suministro_medicamento','material_curacion'].includes(k),full:['motivo_consulta','otro_procedimiento'].includes(k)})).join('')}${sig('firma_usuario','Firma: Usuario')}${sig('firma_enfermeria','Firma: Enfermería')}</div><div class="actions" style="margin-top:22px"><button class="btn primary">Guardar atención</button></div></form></section>`;
 const list=`<section class="paper"><div class="section-title"><h2>Atenciones por mes</h2><div class="actions"><input id="bitacora-mes" type="month" value="${escapeHtml(S.month)}"><button id="filter-bitacora" class="btn secondary sm">Consultar mes</button><button data-pdf="bitacora" data-month="${escapeHtml(S.month)}" class="btn outline sm">${icon('download',16)} Descargar PDF del mes</button></div></div>${table(['No.','Fecha','Hora','Nombre','Matrícula','Motivo de consulta'],rows.map(a=>`<tr><td>${a.id}</td><td>${escapeHtml(a.fecha)}</td><td>${escapeHtml(a.hora)}</td><td>${escapeHtml(a.nombre)}</td><td>${escapeHtml(a.matricula)}</td><td>${escapeHtml(a.datos.motivo_consulta)}</td></tr>`))}</section>`;
 return adminLayout(`<section class="paper"><div class="section-title"><h2>Bitácora de atención</h2><div class="actions"><button type="button" class="btn ${S.bitacoraTab==='new'?'primary':'secondary'} sm" data-bitacora-tab="new">Nueva atención</button><button type="button" class="btn ${S.bitacoraTab==='list'?'primary':'secondary'} sm" data-bitacora-tab="list">Registros guardados (${rows.length})</button></div></div></section>${S.bitacoraTab==='new'?form:list}`,'Bitácora de atención','Formulario y registros en apartados separados');
}
function attentionTable(rows){return table(['No.','Fecha','Hora','Nombre','Matrícula','Motivo de consulta'],rows.map(a=>`<tr><td>${a.id}</td><td>${escapeHtml(a.fecha)}</td><td>${escapeHtml(a.hora)}</td><td>${escapeHtml(a.nombre)}</td><td>${escapeHtml(a.matricula)}</td><td>${escapeHtml(a.datos.motivo_consulta)}</td></tr>`))}

function canalizaciones(rows){
 const f=[['nombre_completo','Nombre completo de la persona'],['nss','NSS','text'],['sexo','Sexo','select'],['edad','Edad','number'],['estado_civil','Estado Civil','select'],['programa_puesto','Carrera / programa / puesto','select'],['matricula_empleado','Matrícula/ No. de empleado'],['telefono_celular','Teléfono celular','tel'],['contacto_emergencia','En caso de emergencia comunicarse con'],['telefono_emergencia','Teléfono en caso de emergencia','tel'],['domicilio','Domicilio'],['correo_electronico','Correo electrónico','email'],['motivo_canalizacion','Motivo de canalización','textarea'],['ta','T/A'],['fc','FC'],['sato2','SatO2'],['fr','FR'],['temperatura','Tª'],['fecha','Fecha','date'],['hora','Hora','time'],['elaboro','Elaboró']];
 const form=`<section class="paper"><h2>Nueva canalización externa</h2><p class="hint" id="referral-header">${referralHeaderText()}</p><form id="referral-form"><div class="form-grid">${studentDropdown(S.referralDraft)}${f.map(([k,l,t])=>bare(k,l,t||'text',{value:S.referralDraft?.[k]??(k==='fecha'?nowDate():k==='hora'?nowTime():k==='elaboro'?S.user?.name||'':''),options:k==='sexo'?['','Hombre','Mujer','Otro','Prefiero no especificar']:k==='estado_civil'?['','Soltero(a)','Casado(a)','Unión libre','Divorciado(a)','Separado(a)','Viudo(a)','Prefiero no especificar']:k==='programa_puesto'?['',...PROGRAMAS_UTGZ,'Personal UTGZ / externo']:[],pattern:k==='nss'?'[0-9]{11}':null,title:k==='nss'?'Escribe los 11 dígitos del NSS':'',required:!['nss','ta','fc','sato2','fr','temperatura'].includes(k),full:['domicilio','motivo_canalizacion'].includes(k)})).join('')}<label class="inline-check full"><input name="consentimiento_informado" type="checkbox" required ${S.referralDraft?.consentimiento_informado?'checked':''}> El estudiante/trabajador(a) acepta haber sido informado y ser canalizado a servicios de salud externos.</label>${sig('firma_responsable','Nombre y firma del Responsable de Enfermería')}${sig('firma_consentimiento','Firma de consentimiento del estudiante/trabajador(a)')}</div><div class="actions" style="margin-top:22px"><button class="btn primary">Guardar canalización</button></div></form></section>`;
 const list=`<section class="paper"><h2>Canalizaciones guardadas</h2><p class="hint">Descarga el PDF o envíalo a contactos autorizados previamente guardados en la base de datos.</p>${table(['No.','Fecha','Nombre','Acciones'],rows.map(a=>`<tr><td>${a.id}</td><td>${escapeHtml(a.fecha)}</td><td>${escapeHtml(a.nombre)}</td><td><div class="actions"><button class="btn sm secondary" data-pdf="canalizacion" data-id="${a.id}">PDF</button><button class="btn sm green" data-sendref="${a.id}">Enviar al correo</button></div></td></tr>`))}</section>`;
 return adminLayout(`<section class="paper"><div class="section-title"><h2>Canalizaciones</h2><div class="actions"><button type="button" class="btn ${S.referralTab==='new'?'primary':'secondary'} sm" data-referral-tab="new">Nueva canalización</button><button type="button" class="btn ${S.referralTab==='list'?'primary':'secondary'} sm" data-referral-tab="list">Registros guardados (${rows.length})</button></div></div></section>${S.referralTab==='new'?form:list}`,'Canalizaciones','Formulario y registros en apartados separados');
}

function sendReferralPage(ident){return adminLayout(`<section class="paper"><div class="section-title"><h2>Enviar canalización #${ident}</h2><button class="btn sm secondary" data-view="canalizaciones">Regresar</button></div><div class="warning-banner">Este PDF contiene datos personales y médicos. Selecciona únicamente destinatarios autorizados por la universidad y confirma que corresponden al propósito de la canalización.</div><form id="send-referral-form" data-id="${ident}"><div class="checks" style="grid-template-columns:repeat(2,minmax(0,1fr))">${S.contacts.filter(c=>c.activo).map(c=>`<label><input type="checkbox" name="contact_ids" value="${c.id}">${escapeHtml(c.nombre)} (${escapeHtml(c.area||'')}): ${escapeHtml(c.correo)}</label>`).join('')}</div><div class="actions"><button class="btn primary">Enviar PDF por correo</button><button class="btn outline" data-view="contactos" type="button">Administrar destinatarios</button></div></form></section>`,'Envío de canalización','Correos almacenados de forma centralizada')}

/* Inventario Inteligente con Semáforo y Filtros */
function inventario(rows){
 const dateToday=nowDate(),period=currentQuarter(),quarter=S.inventoryQuarter===undefined?period:S.inventoryQuarter;
 return adminLayout(`
  <section class="paper">
    <div class="section-title">
      <div>
        <h2>Inventario de medicamento y material de curación existente</h2>
        <p class="hint">El inventario se revisa y exporta cada cuatrimestre. Detecta agotados, stock bajo y caducidades.</p>
      </div>
    </div>
    <form id="inventory-form" data-id="${S.editInventory?.id||''}">
      <div class="form-grid cols3">
        ${bare('medicamento_material','Medicamento/Material de curación','text',{value:S.editInventory?.medicamento_material||''})}
        ${bare('descripcion','Descripción','text',{value:S.editInventory?.descripcion||'',required:false})}
        ${bare('fecha_caducidad','Fecha de caducidad','date',{value:S.editInventory?.fecha_caducidad||dateToday})}
        ${bare('cantidad_inicio','Cantidad: Inicio de cuatrimestre','number',{value:S.editInventory?.cantidad_inicio??0,min:0})}
        ${bare('cantidad_fin','Cantidad: Fin de cuatrimestre','number',{value:S.editInventory?.cantidad_fin??0,min:0})}
        ${bare('stock_minimo','Existencia mínima (alerta de stock bajo)','number',{value:S.editInventory?.stock_minimo??3,min:0})}
        ${bare('cuatrimestre','Cuatrimestre','text',{value:S.editInventory?.cuatrimestre||period})}
      </div>
      <div class="actions" style="margin-top:20px">
        <button class="btn primary">${S.editInventory?'Guardar cambios':'Agregar registro'}</button>
        ${S.editInventory?'<button type="button" class="btn secondary" id="clear-inv">Cancelar edición</button>':''}
      </div>
    </form>
  </section>

  <section class="paper">
    <div class="section-title">
      <div>
        <h2>Existencias y Semáforo de Alertas</h2>
        <p class="hint">Indicadores: <span class="status-dot green"></span>Óptimo · <span class="status-dot yellow"></span>Existencias bajas / Por caducar · <span class="status-dot red"></span>Agotado / Caducado</p>
      </div>
      <button class="btn outline sm" id="export-inv">Descargar reporte cuatrimestral PDF</button>
    </div>

    <div class="searchline">
      <input id="inventory-quarter" value="${escapeHtml(quarter)}" aria-label="Cuatrimestre a consultar">
      <button class="btn sm secondary" id="filter-inv">Consultar periodo</button>
    </div>

    <div class="filter-pills">
      <button class="filter-pill ${!S.inventoryFilter?'active':''}" data-invfilter="">Todos (${rows.length})</button>
      <button class="filter-pill ${S.inventoryFilter==='criticos'?'active':''}" data-invfilter="criticos">${icon('alert-triangle',14)} Alertas / Críticos</button>
      <button class="filter-pill ${S.inventoryFilter==='agotados'?'active':''}" data-invfilter="agotados"><span class="status-dot red"></span>Agotados</button>
      <button class="filter-pill ${S.inventoryFilter==='stock_bajo'?'active':''}" data-invfilter="stock_bajo"><span class="status-dot yellow"></span>Stock bajo</button>
      <button class="filter-pill ${S.inventoryFilter==='por_caducar'?'active':''}" data-invfilter="por_caducar"><span class="status-dot orange"></span>Próximos a caducar</button>
      <button class="filter-pill ${S.inventoryFilter==='optimo'?'active':''}" data-invfilter="optimo"><span class="status-dot green"></span>Óptimos</button>
    </div>

    ${table(['Estado','Medicamento/Material','Descripción','Caducidad','Inicio','Fin','Mín.','Cuatrimestre','Acción'],rows.map(a=>{
      const est = a.estado_stock || {estado:'optimo', color:'verde', etiqueta:'Óptimo'};
      const dotColor = est.color==='verde'?'green':est.color==='amarillo'?'yellow':'red';
      return `<tr>
        <td><span class="status-dot ${dotColor}"></span><span class="pill ${est.estado}">${escapeHtml(est.etiqueta)}</span></td>
        <td><b>${escapeHtml(a.medicamento_material)}</b></td>
        <td>${escapeHtml(a.descripcion)}</td>
        <td>${escapeHtml(a.fecha_caducidad)}</td>
        <td>${a.cantidad_inicio}</td>
        <td><b>${a.cantidad_fin}</b></td>
        <td>${a.stock_minimo??3}</td>
        <td>${escapeHtml(a.cuatrimestre)}</td>
        <td><button class="btn sm secondary" data-editinv="${a.id}">Editar</button></td>
      </tr>`;
    }))}
  </section>
 `,'Inventario inteligente','Control cuatrimestral con semáforo y existencias mínimas');
}

function contactos(rows){return adminLayout(`<section class="paper"><h2>${S.editContact?'Editar destinatario de correo':'Agregar destinatario de correo'}</h2><p class="hint">Solo el administrador puede agregar o modificar destinatarios de canalizaciones.</p><form id="contact-form" data-id="${S.editContact?.id||''}"><div class="form-grid cols3">${bare('nombre','Nombre del destinatario','text',{value:S.editContact?.nombre||''})}${bare('correo','Correo electrónico','email',{value:S.editContact?.correo||''})}${bare('area','Área / Jefatura de carrera','text',{required:false,value:S.editContact?.area||''})}</div><div class="actions" style="margin-top:20px;display:flex;gap:10px"><button class="btn primary">${S.editContact?'Actualizar correo':'Guardar correo'}</button>${S.editContact?'<button type="button" class="btn secondary" id="clear-contact">Cancelar edición</button>':''}</div></form></section><section class="paper"><h2>Correos guardados</h2>${table(['Nombre','Correo electrónico','Área','Estado','Acciones'],rows.map(a=>`<tr><td>${escapeHtml(a.nombre)}</td><td>${escapeHtml(a.correo)}</td><td>${escapeHtml(a.area)}</td><td><span class="pill ${!a.activo?'warn':''}">${a.activo?'Activo':'Inactivo'}</span></td><td style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn sm secondary" data-contact-edit="${a.id}">Editar</button><button class="btn sm secondary" data-contact-toggle="${a.id}">${a.activo?'Desactivar':'Activar'}</button><button class="btn sm danger" data-contact-delete="${a.id}" title="Eliminar correo de la base de datos">Eliminar</button></td></tr>`))}</section>`,'Destinatarios guardados','Correos de jefaturas de carrera y personal autorizado')}

async function checkGoogleAuthConfig(){
  try {
    const conf = await api('/api/auth/google/config');
    if (conf && conf.enabled) {
      const gSec = $('#google-auth-container');
      if (gSec) gSec.style.display = '';
      const gIntro = $('#login-intro-text');
      if (gIntro) gIntro.textContent = 'Accede con tu cuenta institucional de Google o con tu contraseña.';
      const gHint = $('#login-hint-text');
      if (gHint) gHint.textContent = 'El acceso por Google está restringido exclusivamente a cuentas registradas en la base de datos de Enfermería.';
    }
  } catch {}
}

async function view(v){S.view=v;S.selectedId=null;const root=$('#app');if(!root)return;
 if(v==='inicio'){root.innerHTML=welcome();history.replaceState({},'', '/');return}
 if(v==='login'){
   if(S.user){await view('dashboard');return}
   root.innerHTML=login();history.replaceState({},'', '/login');
   checkGoogleAuthConfig();
   return;
 }
 if(v==='alumno'){root.innerHTML=student();setupSignatures();updateAge();history.replaceState({},'', '/alumno');return}
 if(!S.user){S.view='login';root.innerHTML=login();checkGoogleAuthConfig();return}
 const viewUrl = v==='dashboard'?'/enfermeria':`/${v}`;
 history.replaceState({},'', viewUrl);
 root.innerHTML=adminLayout('<div class="paper"><p class="muted">Cargando registros…</p></div>','Enfermería','SAMU UTGZ');
 try{
  let html='';
  if(v==='dashboard'){const data=await api('/api/resumen');html=dashboard(data)}
  if(v==='fichas'){S.rows=await api('/api/fichas');html=fichas(S.rows)}
  if(v==='importar'){html=importarView(S.importPreview)}
  if(v==='bitacora'){[S.rows,S.students]=await Promise.all([api(`/api/bitacora?mes=${encodeURIComponent(S.month)}`),api('/api/estudiantes')]);html=bitacora(S.rows)}
  if(v==='canalizaciones'){[S.rows,S.students]=await Promise.all([api('/api/canalizaciones'),api('/api/estudiantes')]);html=canalizaciones(S.rows)}
  if(v==='inventario'){
    if(S.inventoryQuarter===undefined)S.inventoryQuarter=currentQuarter();
    const p=new URLSearchParams({cuatrimestre:S.inventoryQuarter,filtro_estado:S.inventoryFilter||''});
    S.rows=await api(`/api/inventario?${p}`);
    html=inventario(S.rows);
  }
  if(v==='contactos'){S.contacts=await api('/api/contactos');html=contactos(S.contacts)}
  if(v==='consultar_estado'){html=consultarEstadoView()}
  if(html){root.innerHTML=html;setupSignatures()}
 }catch(e){root.innerHTML=adminLayout(`<section class="paper"><div class="warning-banner">${escapeHtml(e.message)}</div><button class="btn secondary" data-view="dashboard">Volver al inicio</button></section>`,'Error','No se pudo cargar el módulo')}
}

function saveStep(){const form=$('#student-form');if(!form)return;for(const [k,v] of new FormData(form)){if(['antecedentes_familiares','antecedentes_personales','edad_calculada'].includes(k))continue;S.draft[k]=v}for(const k of ['antecedentes_familiares','antecedentes_personales']){if(form.querySelector(`[name=${k}]`))S.draft[k]=[...form.querySelectorAll(`[name=${k}]:checked`)].map(i=>i.value)}if(S.step===6){S.draft.autoriza_traslado=!!form.querySelector('[name=autoriza_traslado]')?.checked;S.draft.firma_aspirante=S.signatures.firma_aspirante||'';if(S.signatures.firma_padre_tutor)S.draft.firma_padre_tutor=S.signatures.firma_padre_tutor}}
function setupSignatures(){S.signatures={};$$('[data-signature]').forEach(container=>{const name=container.dataset.signature;const c=container.querySelector('canvas');if(!c)return;const ctx=c.getContext('2d');ctx.lineCap='round';ctx.lineJoin='round';ctx.strokeStyle='#28684f';ctx.lineWidth=3.3;let down=false,drawn=false,last=null;function coords(e){const r=c.getBoundingClientRect();return{x:(e.clientX-r.left)*c.width/r.width,y:(e.clientY-r.top)*c.height/r.height}};
 const prev=S.draft[name];if(prev){const im=new Image;im.onload=()=>{ctx.drawImage(im,0,0,c.width,c.height);S.signatures[name]=prev;drawn=true};im.src=prev}
 c.addEventListener('pointerdown',e=>{e.preventDefault();c.setPointerCapture(e.pointerId);down=true;drawn=true;last=coords(e);ctx.beginPath();ctx.moveTo(last.x,last.y);ctx.lineTo(last.x+.02,last.y+.02);ctx.stroke()});
 c.addEventListener('pointermove',e=>{if(!down)return;e.preventDefault();const q=coords(e);ctx.beginPath();ctx.moveTo(last.x,last.y);ctx.lineTo(q.x,q.y);ctx.stroke();last=q});
 const stop=e=>{if(!down)return;down=false;if(drawn)S.signatures[name]=c.toDataURL('image/png')};c.addEventListener('pointerup',stop);c.addEventListener('pointercancel',stop);c.addEventListener('lostpointercapture',stop);
 container.querySelector('[data-clear]')?.addEventListener('click',()=>{ctx.clearRect(0,0,c.width,c.height);S.signatures[name]='';drawn=false;last=null});
})}
async function download(kind,id,cuatrimestre,mes){try{const r=await api('/api/descargas',{method:'POST',data:{tipo:kind,id:id||null,cuatrimestre:cuatrimestre||'',mes:mes||''}});const a=document.createElement('a');a.href=r.url;a.target='_blank';a.rel='noopener';document.body.append(a);a.click();a.remove();toast('PDF listo para descargar. El enlace es de un solo uso.')}catch(e){parseErr(e)}}
async function imageToData(file){if(!file)return '';if(!['image/jpeg','image/png'].includes(file.type))throw Error('Usa una fotografía JPG o PNG.');const im=new Image;const uri=await new Promise((resolve,reject)=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file)});await new Promise((resolve,reject)=>{im.onload=resolve;im.onerror=reject;im.src=uri});const scale=Math.min(1,1000/Math.max(im.width,im.height));const c=document.createElement('canvas');c.width=Math.floor(im.width*scale);c.height=Math.floor(im.height*scale);c.getContext('2d').drawImage(im,0,0,c.width,c.height);return c.toDataURL('image/jpeg',.78)}

function applyPrefill(){
  const selected=$('#pick-student');
  if(!selected)return;
  const item=S.students.find(x=>String(x.id)===selected.value);
  const alertsBox=$('#picked-student-alerts');
  if(alertsBox){
    alertsBox.innerHTML=item?.alertas_medicas?medicalAlertsHtml(item.alertas_medicas):'';
  }
  if(!item)return;
  const form=selected.closest('form');
  if(form.id==='bitacora-form'){
    form.elements.nombre.value=item.nombre;
    form.elements.matricula.value=item.matricula||'';
    form.elements.programa_educativo.value=item.programa_educativo||'';
    if(form.elements.grupo&&item.grupo)form.elements.grupo.value=item.grupo;
  }
  if(form.id==='referral-form'){
    form.elements.nombre_completo.value=item.nombre;
    form.elements.nss.value=item.nss||'';
    form.elements.matricula_empleado.value=item.matricula||'';
    form.elements.correo_electronico.value=item.correo||'';
    form.elements.contacto_emergencia.value=item.contacto_emergencia||'';
    form.elements.telefono_emergencia.value=item.telefono_emergencia||'';
    form.elements.programa_puesto.value=item.programa_educativo||'';
  }
  if(form.elements.edad&&item.edad!=null)form.elements.edad.value=item.edad;
  if(form.elements.sexo)form.elements.sexo.value=item.sexo||'';
}

document.addEventListener('change',async e=>{
 if(e.target?.id==='pick-student')applyPrefill();
 if(e.target?.name==='fecha_nacimiento')updateAge();
 if(e.target?.name==='fecha'&&e.target.closest('#referral-form')){const el=$('#referral-header');if(el)el.textContent=referralHeaderText(e.target.value)}
 if(e.target?.id==='import-file'){
   const file=e.target.files?.[0];
   if(!file)return;
   S.importFile=file;
   const nameEl=$('#file-chosen-name');if(nameEl)nameEl.textContent=`Procesando: ${file.name}…`;
   try{
     const fd=new FormData();
     fd.append('file',file);
     const preview=await api('/api/estudiantes/importar/preview',{method:'POST',body:fd});
     S.importPreview=preview;
     $('#app').innerHTML=importarView(preview);
     toast(`Vista previa generada: ${preview.total} registros encontrados`);
   }catch(err){parseErr(err);if(nameEl)nameEl.textContent=''}
 }
});

document.addEventListener('input',e=>{if(e.target?.name==='fecha_nacimiento')updateAge()});

document.addEventListener('click',async e=>{
 const t=e.target.closest('button,[data-view],[data-invfilter],[data-bitacora-tab],[data-referral-tab],[data-editfiche],[data-cancel-edit],.quick-card,#btn-browse-file,#btn-confirm-import,#btn-cancel-import');
 if(!t)return;

 if(t.dataset.themeToggle!==undefined){setTheme(!S.dark);return}

 if(t.id==='btn-google-login'){
   t.disabled=true;
   const origHtml=t.innerHTML;
   t.innerHTML=`${icon('google',20)}<span>Conectando con Google…</span>`;
   try{
     const conf=await api('/api/auth/google/config');
     if(!conf.enabled){
       t.disabled=false;
       t.innerHTML=origHtml;
       toast('El inicio de sesión con Google requiere configurar GOOGLE_CLIENT_ID en el servidor (.env).',true);
       return;
     }
     const r=await api('/api/auth/google/url');
     if(!r.url)throw Error('No se pudo generar la URL de autenticación de Google');

     const authWindow=window.open(r.url,'_blank');
     if(!authWindow || authWindow.closed || typeof authWindow.closed==='undefined'){
       window.location.href=r.url;
       return;
     }

     t.innerHTML=`${icon('google',20)}<span>Esperando autorización…</span>`;
     toast('Completa tu inicio de sesión en Google.');

     let attempts=0;
     const maxAttempts=120;
     const pollInterval=setInterval(async()=>{
       attempts++;
       if(attempts>maxAttempts){
         clearInterval(pollInterval);
         t.disabled=false;
         t.innerHTML=origHtml;
         toast('Tiempo de espera agotado. Intenta de nuevo.',true);
         return;
       }
       try{
         const poll=await api(`/api/auth/google/poll-session?state=${encodeURIComponent(r.state)}`);
         if(poll.status==='authenticated'){
           clearInterval(pollInterval);
           try{if(authWindow&&!authWindow.closed)authWindow.close()}catch{}
           t.innerHTML=`${icon('google',20)}<span>Verificando permisos…</span>`;
           const fin=await api('/api/auth/google/finalize-session',{
             method:'POST',
             data:{state:r.state,exchange_token:poll.exchange_token}
           });
           if(fin.role==='student'){
             // Estudiante autenticado con Google: mostrar credencial directamente
             window.currentStudentSession={student_id:fin.student.student_id,session_token:fin.student.session_token};
             const root=$('#app');
             root.innerHTML=frame(`
               <div class="student-container">
                 <div class="student-lead">
                   <div><span class="eyebrow">Credencial Digital SAMU</span><h1>Hola, ${escapeHtml(fin.student.nombre_estudiante)}</h1><p class="muted">Verificado con Google. Esta es tu credencial oficial SAMU UTGZ.</p></div>
                   <img src="${logo}" alt="Samu">
                 </div>
                 <div id="resultado-credencial-card">${renderCredencialCard(fin.student)}</div>
               </div>`,true);
             if(window.QRCode){
               new QRCode($('#qrcode-container'),{text:fin.student.qr_token,width:170,height:170,colorDark:'#123424',colorLight:'#ffffff',correctLevel:QRCode.CorrectLevel.M});
             }else{
               const c=$('#qrcode-container');if(c)c.innerHTML=`<img src="https://api.qrserver.com/v1/create-qr-code/?size=170x170&data=${encodeURIComponent(fin.student.qr_token)}" alt="Codigo QR">`;
             }
             toast('Sesion iniciada con Google. Tu credencial esta lista.');
             history.replaceState({},'','/consultar-estado');
           }else{
             S.user=fin.user;
             S.csrf=fin.csrf;
             toast(`Bienvenida(o), ${fin.user.name}`);
             await view('dashboard');
           }
         }else if(poll.status==='unauthorized'){
           clearInterval(pollInterval);
           try{if(authWindow&&!authWindow.closed)authWindow.close()}catch{}
           t.disabled=false;
           t.innerHTML=origHtml;
           toast(poll.detail||'Tu cuenta no tiene permisos autorizados de enfermería.',true);
         }else if(poll.status==='error'){
           clearInterval(pollInterval);
           try{if(authWindow&&!authWindow.closed)authWindow.close()}catch{}
           t.disabled=false;
           t.innerHTML=origHtml;
           toast(poll.detail||'Error durante la autenticación con Google.',true);
         }
       }catch(pollErr){}
     },1500);
   }catch(err){
     t.disabled=false;
     t.innerHTML=origHtml;
     parseErr(err);
   }
   return;
 }

 if(t.id==='btn-request-otp'){
   const correo=(S.draft.correo||$('#student-form')?.elements?.correo?.value||'').trim();
   const nombre=(S.draft.nombre_aspirante||$('#student-form')?.elements?.nombre_aspirante?.value||'').trim();
   const matricula=(S.draft.matricula||$('#student-form')?.elements?.matricula?.value||'').trim();
   const sitio_web=($('#student-form')?.elements?.sitio_web?.value||'').trim();
   if(!correo){
     toast('Ingresa tu correo en el paso 1 antes de solicitar el código.',true);
     return;
   }
   t.disabled=true;
   const origHtml=t.innerHTML;
   t.innerHTML=`${icon('mail',16)} Enviando código…`;
   try{
     let csrfToken=S.csrf;
     if(!csrfToken){
       try{
         const c=await api('/api/csrf-public');
         csrfToken=c.csrf;
         S.csrf=csrfToken;
       }catch{}
     }
     const res=await api('/api/alumnos/verificar-correo/solicitar',{
       method:'POST',
       data:{correo,nombre,matricula:matricula||null,sitio_web},
       headers:csrfToken?{'X-CSRF-Token':csrfToken}:{}
     });
     toast(res.mensaje||'Código enviado. Revisa tu bandeja de entrada o spam.');
     const timerMsg=$('#otp-timer-msg');
     let cd=60;
     t.textContent=`Reenviar en ${cd}s`;
     const interval=setInterval(()=>{
       cd--;
       if(cd<=0){
         clearInterval(interval);
         t.disabled=false;
         t.innerHTML=origHtml;
         if(timerMsg)timerMsg.textContent='';
       }else{
         t.textContent=`Reenviar en ${cd}s`;
         if(timerMsg)timerMsg.textContent=`Puedes solicitar otro código en ${cd}s`;
       }
     },1000);
   }catch(err){
     t.disabled=false;
     t.innerHTML=origHtml;
     parseErr(err);
   }
   return;
 }

 if(t.dataset.view){
   e.preventDefault();
   if(t.dataset.bitacoraTab)S.bitacoraTab=t.dataset.bitacoraTab;
   if(t.dataset.referralTab)S.referralTab=t.dataset.referralTab;
   view(t.dataset.view);
   return;
 }
 if(t.id==='btn-browse-file'){$('#import-file')?.click();return}
 if(t.id==='btn-cancel-import'){S.importFile=null;S.importPreview=null;$('#app').innerHTML=importarView(null);return}

 if(t.id==='btn-confirm-import'){
   if(!S.importFile){toast('Selecciona un archivo primero.',true);return}
   const updateDup=$('#chk-update-dup')?.checked??true;
   t.disabled=true;t.textContent='Importando alumnos…';
   try{
     const fd=new FormData();
     fd.append('file',S.importFile);
     fd.append('actualizar_duplicados',updateDup?'true':'false');
     const res=await api('/api/estudiantes/importar',{method:'POST',body:fd});
     toast(`Importación finalizada: ${res.creados} nuevos creados, ${res.actualizados} actualizados.`);
     S.importFile=null;S.importPreview=null;
     view('fichas');
   }catch(err){parseErr(err);t.disabled=false;t.textContent='Confirmar e importar estudiantes'}
   return;
 }

 if(t.dataset.invfilter!==undefined){
   S.inventoryFilter=t.dataset.invfilter;
   try{
     const p=new URLSearchParams({cuatrimestre:S.inventoryQuarter||currentQuarter(),filtro_estado:S.inventoryFilter});
     S.rows=await api(`/api/inventario?${p}`);
     $('#app').innerHTML=inventario(S.rows);
   }catch(err){parseErr(err)}
   return;
 }

 if(t.dataset.history){
   try{
     const histData=await api(`/api/fichas/${t.dataset.history}/historial`);
     $('#app').innerHTML=renderHistory(histData);
   }catch(err){parseErr(err)}
   return;
 }

 if(t.id==='hist-filter-btn'){
   const stId=t.dataset.studentid;
   const periodo=$('#hist-periodo')?.value||'';
   try{
     const histData=await api(`/api/fichas/${stId}/historial?mes=${encodeURIComponent(periodo)}`);
     $('#app').innerHTML=renderHistory(histData);
     if(periodo)$('#hist-periodo').value=periodo;
   }catch(err){parseErr(err)}
   return;
 }

 if(t.id==='hist-clear-btn'){
   const stId=t.dataset.studentid;
   try{
     const histData=await api(`/api/fichas/${stId}/historial`);
     $('#app').innerHTML=renderHistory(histData);
   }catch(err){parseErr(err)}
   return;
 }

 if(t.dataset.bitacoraTab){
   const form=$('#bitacora-form');
   if(form){
     S.bitacoraDraft=obj(form);
     for(const name of ['firma_usuario','firma_enfermeria'])S.draft[name]=S.signatures[name]||'';
   }
   S.bitacoraTab=t.dataset.bitacoraTab;
   $('#app').innerHTML=bitacora(S.rows);
   setupSignatures();
   return;
 }
 if(t.dataset.referralTab){const form=$('#referral-form');if(form){S.referralDraft=obj(form);S.referralDraft.consentimiento_informado=!!form.querySelector('[name=consentimiento_informado]').checked;for(const name of ['firma_responsable','firma_consentimiento'])S.draft[name]=S.signatures[name]||''}S.referralTab=t.dataset.referralTab;$('#app').innerHTML=canalizaciones(S.rows);setupSignatures();return}
 if(t.dataset.editfiche){
   try{
     S.editingFicheId=Number(t.dataset.editfiche);
     const a=await api(`/api/fichas/${t.dataset.editfiche}`);
     $('#app').innerHTML=ficheEdit(a);
     scrollTo({top:0,behavior:'smooth'});
   }catch(err){parseErr(err)}
   return;
 }
 if(t.dataset.cancelEdit){
   try{
     S.editingFicheId=null;
     const a=await api(`/api/fichas/${t.dataset.cancelEdit}`);
     $('#app').innerHTML=ficheDetail(a);
   }catch(err){parseErr(err)}
   return;
 }
 if(t.id==='logout'){try{await api('/api/session/logout',{method:'POST'});S.user=null;S.csrf='';toast('Sesión cerrada');view('login')}catch(err){parseErr(err)}return}
 if(t.id==='student-prev'){saveStep();S.step=Math.max(0,S.step-1);view('alumno');return}
 if(t.dataset.ficha){try{const a=await api(`/api/fichas/${t.dataset.ficha}`);$('#app').innerHTML=ficheDetail(a);S.view='fichas'}catch(err){parseErr(err)}return}
 if(t.id==='fichas-search'){try{const p=new URLSearchParams({q:$('#fichas-q').value,estado:$('#fichas-estado').value});S.rows=await api(`/api/fichas?${p}`);const q=$('#fichas-q').value,z=$('#fichas-estado').value;$('#app').innerHTML=fichas(S.rows);$('#fichas-q').value=q;$('#fichas-estado').value=z}catch(err){parseErr(err)}return}
 if(t.dataset.pdf){const mes=t.dataset.pdf==='bitacora'?$('#bitacora-mes')?.value:t.dataset.month;download(t.dataset.pdf,t.dataset.id,$('#inventory-quarter')?.value,mes);return}
 if(t.dataset.sendref){try{S.contacts=await api('/api/contactos');$('#app').innerHTML=sendReferralPage(t.dataset.sendref)}catch(err){parseErr(err)}return}
 if(t.dataset.editinv){S.editInventory=S.rows.find(r=>String(r.id)===t.dataset.editinv);$('#app').innerHTML=inventario(S.rows);scrollTo({top:0,behavior:'smooth'});return}
 if(t.id==='clear-inv'){S.editInventory=null;$('#app').innerHTML=inventario(S.rows);return}
 if(t.id==='filter-inv'){try{const v=$('#inventory-quarter').value;S.inventoryQuarter=v;const p=new URLSearchParams({cuatrimestre:v,filtro_estado:S.inventoryFilter||''});S.rows=await api(`/api/inventario?${p}`);$('#app').innerHTML=inventario(S.rows)}catch(err){parseErr(err)}return}
 if(t.id==='export-inv'){download('inventario',null,$('#inventory-quarter').value);return}
 if(t.id==='filter-bitacora'){try{S.month=$('#bitacora-mes').value;if(!S.month)throw Error('Selecciona el mes que quieres consultar.');S.rows=await api(`/api/bitacora?mes=${encodeURIComponent(S.month)}`);const section=t.closest('.paper'),tableWrap=section?.querySelector('.table-wrap');if(tableWrap)tableWrap.outerHTML=attentionTable(S.rows)}catch(err){parseErr(err)}return}
 if(t.dataset.contactEdit){S.editContact=S.contacts.find(r=>String(r.id)===t.dataset.contactEdit);$('#app').innerHTML=contactos(S.contacts);scrollTo({top:0,behavior:'smooth'});return}
 if(t.id==='btn-pedir-otp-consulta'){
   const correo = ($('#correo_consulta')?.value||'').trim();
   if(!correo || !correo.includes('@')){toast('Ingresa un correo electrónico válido.', true); return}
   t.disabled = true;
   t.textContent = 'Enviando código…';
   try {
     let csrfToken = S.csrf;
     if(!csrfToken){ try{ const c=await api('/api/csrf-public'); csrfToken=c.csrf; S.csrf=csrfToken }catch{} }
     await api('/api/alumnos/verificar-correo', {
       method: 'POST',
       data: { correo },
       headers: csrfToken ? {'X-CSRF-Token': csrfToken} : {}
     });
     toast('Código de verificación enviado a tu correo.');
     $('#form-verificar-consulta').style.display = 'block';
     $('#correo_consulta').readOnly = true;
     t.style.display = 'none';
   } catch(err){
     toast(err.message || 'Error al enviar código', true);
     t.disabled = false;
     t.textContent = 'Enviar código a mi correo';
   }
   return;
 }
 if(t.id==='btn-cambiar-correo-consulta'){
   $('#form-verificar-consulta').style.display = 'none';
   $('#correo_consulta').readOnly = false;
   const btnPedir = $('#btn-pedir-otp-consulta');
   if(btnPedir){ btnPedir.disabled = false; btnPedir.style.display = 'inline-flex'; btnPedir.textContent = 'Enviar código a mi correo'; }
   return;
 }
 if(t.id==='btn-open-qr-scanner' || t.id==='btn-dashboard-scan-qr' || t.closest('#btn-dashboard-scan-qr')){
   const modalHtml = renderQrScannerModal();
   document.body.insertAdjacentHTML('beforeend', modalHtml);
   startQrCamera();
   return;
 }
 if(t.id==='btn-close-scanner'){
   stopQrCamera();
   $('#qr-scanner-modal')?.remove();
   return;
 }
 if(t.id==='btn-manual-qr-search'){
   const token = ($('#manual-qr-token')?.value || '').trim();
   if(!token){ toast('Ingresa el folio o código del QR', true); return; }
   stopQrCamera();
   $('#qr-scanner-modal')?.remove();
   processScannedToken(token);
   return;
 }
 if(t.id==='btn-regenerar-qr'){
   const id = t.dataset.id;
   if(!id || !confirm('¿Deseas revocar el QR actual y generar un nuevo identificador para este alumno?')) return;
   try {
     const res = await api(`/api/fichas/${id}/regenerar-qr`, { method: 'POST' });
     toast('Nuevo código QR generado con éxito');
     const f = await api(`/api/fichas/${id}`);
     $('#app').innerHTML = ficheDetail(f);
   } catch(err){ parseErr(err); }
   return;
 }
 if(t.id==='fichas-search'){
   const q = ($('#fichas-q')?.value||'').trim();
   const est = ($('#fichas-estado')?.value||'').trim();
   try {
     const p = new URLSearchParams();
     if(q) p.set('q', q);
     if(est) p.set('estado', est);
     S.rows = await api(`/api/fichas?${p.toString()}`);
     const sec = t.closest('.paper');
     const tw = sec?.querySelector('.table-wrap');
     if(tw) tw.outerHTML = table(['Folio','Aspirante / Estudiante','Matrícula','Estado','Registro','Acciones'],S.rows.map(r=>`<tr><td>${escapeHtml(r.folio)}</td><td>${escapeHtml(r.nombre_aspirante)}</td><td>${escapeHtml(r.matricula||'—')}</td><td>${badgeEstadoFicha(r.estado)}</td><td>${escapeHtml((r.created||'').slice(0,10))}</td><td><div class="actions"><button class="btn sm secondary" data-ficha="${r.id}">Revisar</button><button class="btn sm green" data-editfiche="${r.id}">Editar</button></div></td></tr>`));
   } catch(err){ parseErr(err); }
   return;
 }
 if(t.id==='tab-student-credencial'||t.id==='tab-student-avisos'||t.id==='tab-student-contacto'){
    ['tab-student-credencial','tab-student-avisos','tab-student-contacto'].forEach(id=>{const el=document.getElementById(id);if(el)el.classList.remove('active');});
    ['panel-student-credencial','panel-student-avisos','panel-student-contacto'].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display='none';});
    t.classList.add('active');
    const pmap={'tab-student-credencial':'panel-student-credencial','tab-student-avisos':'panel-student-avisos','tab-student-contacto':'panel-student-contacto'};
    const p=document.getElementById(pmap[t.id]);if(p)p.style.display='block';
    return;
  }
 if(t.id==='btn-sync-now'){syncPendingQueue();return}
 if(t.dataset.contactToggle){const a=S.contacts.find(r=>String(r.id)===t.dataset.contactToggle);if(!a)return;try{await api(`/api/contactos/${a.id}`,{method:'PUT',data:{...a,activo:!a.activo}});toast('Destinatario actualizado.');view('contactos')}catch(err){parseErr(err)}return}
 if(t.dataset.contactDelete){const a=S.contacts.find(r=>String(r.id)===t.dataset.contactDelete);if(!a)return;if(!confirm(`¿Deseas eliminar a "${a.nombre}" (${a.correo}) de la lista de destinatarios?`))return;try{const res=await api(`/api/contactos/${a.id}`,{method:'DELETE'});toast(res?.message||'Correo eliminado de la base de datos.');view('contactos')}catch(err){parseErr(err)}return}
});

document.addEventListener('submit',async e=>{
 const form=e.target;if(!['login-form','student-form','validate-form','student-email-form','bitacora-form','referral-form','inventory-form','contact-form','send-referral-form','edit-fiche-form','form-verificar-consulta','form-cambiar-estado'].includes(form.id))return;e.preventDefault();const btn=form.querySelector('button[type=submit],button:not([type])');if(btn)btn.disabled=true;
 try{
  if(form.id==='form-verificar-consulta'){
    const correo = ($('#correo_consulta')?.value||'').trim();
    const codigo = ($('#input-codigo-consulta')?.value||'').trim();
    if(!codigo || codigo.length < 6) throw Error('Ingresa el código de 6 dígitos enviado a tu correo.');
    const res = await api('/api/alumnos/consultar-estado', {
      method: 'POST',
      data: { correo, codigo_verificacion: codigo }
    });
    if(!res.ok) throw Error('No se pudo consultar el estado.');
    $('#estado-check-card').style.display = 'none';
    const resCard = $('#resultado-credencial-card');
    resCard.style.display = 'block';
    resCard.innerHTML = renderCredencialCard(res);
    // Generar código QR con la librería cliente QRCode
    if(window.QRCode){
      new QRCode($('#qrcode-container'), {
        text: res.qr_token,
        width: 170,
        height: 170,
        colorDark: '#123424',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.M
      });
    } else {
      $('#qrcode-container').innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=170x170&data=${encodeURIComponent(res.qr_token)}" alt="Código QR">`;
    }
    toast('¡Identidad verificada! Credencial Digital generada.');
    return;
  }
  if(form.id==='form-cambiar-estado'){
    const estado = form.elements.estado.value;
    const obs = form.elements.observaciones_correccion ? form.elements.observaciones_correccion.value : '';
    await api(`/api/fichas/${form.dataset.id}/estado`, {
      method: 'POST',
      data: { estado, observaciones_correccion: obs }
    });
    toast('Estado de la ficha médica actualizado correctamente.');
    const a = await api(`/api/fichas/${form.dataset.id}`);
    $('#app').innerHTML = ficheDetail(a);
    return;
  }
  if(form.id==='login-form'){const d=obj(form);const r=await api('/api/session/login',{method:'POST',data:d});S.user=r.user;S.csrf=r.csrf;toast('Bienvenido al panel de enfermería');await view('dashboard')}
  if(form.id==='student-form'){
    if(S.step<7){
      saveStep();
      if(S.step===0){
        if(!S.draft.nombre_aspirante?.trim())throw Error('Ingresa el nombre completo del estudiante.');
        if(!S.draft.correo?.trim())throw Error('Ingresa un correo electrónico de contacto.');
        const emailRegex=/^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if(!emailRegex.test(S.draft.correo.trim()))throw Error('Ingresa un correo electrónico con formato válido.');
      }
      if(S.step===6){
        if(!S.draft.autoriza_traslado)throw Error('Es necesario marcar la autorización de traslado.');
        if(!S.draft.firma_aspirante)throw Error('Debes registrar tu firma digital.');
      }
      S.step++;
      await view('alumno');
    }
    else {
      saveStep();
      const codigo=form.elements.codigo_verificacion?.value?.trim();
      if(!codigo||codigo.length<6)throw Error('Ingresa el código de 6 dígitos que enviamos a tu correo.');
      const aceptaAviso=!!(form.elements.acepto_aviso?.checked||form.elements.acepta_privacidad?.checked||$('#acepto_aviso')?.checked||$('#acepta-privacidad')?.checked);
      if(!aceptaAviso)throw Error('Debes confirmar que has leído el aviso de privacidad.');
      const d={...S.draft,...obj(form),codigo_verificacion:codigo};
      delete d.student_id;
      let csrfToken=S.csrf;
      if(!csrfToken){
        try{
          const c=await api('/api/csrf-public');
          csrfToken=c.csrf;
          S.csrf=csrfToken;
        }catch{}
      }
      const r=await api('/api/alumnos/ficha',{
        method:'POST',
        data:d,
        headers:csrfToken?{'X-CSRF-Token':csrfToken}:{}
      });
      S.draft={};
      S.signatures={};
      S.step=0;
      $('#app').innerHTML=frame(`
        <main class="student-container">
          <section class="paper" style="text-align:center;padding:48px 24px;max-width:680px;margin:30px auto;">
            <div style="width:72px;height:72px;background:var(--mint);border-radius:50%;color:var(--navy);display:inline-flex;align-items:center;justify-content:center;margin:0 auto 20px;">
              ${icon('check-circle',42)}
            </div>
            <h1 style="color:var(--navy2);font-size:1.8rem;margin:0 0 10px;">¡Ficha médica registrada con éxito!</h1>
            <p style="color:var(--muted);font-size:1.02rem;margin:0 0 24px;line-height:1.5;">
              Tu información ha sido resguardada con confidencialidad médica en el sistema SAMU de la UTGZ.
            </p>
            
            <div style="background:var(--mint);border:1.5px solid var(--line);border-radius:14px;padding:24px 20px;max-width:460px;margin:0 auto 28px;box-shadow:0 4px 14px rgba(40,104,79,0.06);">
              <span style="font-size:0.85rem;color:var(--muted);display:block;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;">Folio oficial de registro</span>
              <strong style="font-size:2rem;color:var(--navy);letter-spacing:2px;display:block;margin:8px 0;font-family:monospace;">${escapeHtml(r.folio)}</strong>
              <p style="font-size:0.88rem;color:var(--muted);margin:4px 0 0;">Conserva este folio para cualquier trámite o atención en el consultorio universitario.</p>
            </div>

            <div style="text-align:left;background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:28px;font-size:0.9rem;color:inherit;">
              <h4 style="margin:0 0 8px;color:var(--navy);display:flex;align-items:center;gap:6px;">
                ${icon('info',16)} Siguientes pasos:
              </h4>
              <ul style="margin:0;padding-left:20px;line-height:1.6;color:var(--muted);">
                <li>El personal de Enfermería revisará y validará tu expediente clínico.</li>
                <li>Si eres de nuevo ingreso y aún no cuentas con matrícula, se te asignará cuando acudas al consultorio.</li>
                <li>Por tu seguridad y privacidad, los datos médicos registrados no se muestran públicamente.</li>
              </ul>
            </div>

            <div>
              <button class="btn primary" data-view="inicio" style="padding:12px 28px;font-size:1rem;">
                Volver a la página principal
              </button>
            </div>
          </section>
        </main>`,true);
    }
  }
  if(form.id==='validate-form'){let d={matricula:form.elements.matricula.value,correo:form.elements.correo.value};const file=$('#foto-alumno')?.files[0];if(file)d.foto=await imageToData(file);await api(`/api/fichas/${form.dataset.id}/validar`,{method:'POST',data:d});toast('Ficha validada correctamente');await view('fichas')}
  if(form.id==='student-email-form'){await api(`/api/fichas/${form.dataset.id}/correo`,{method:'PUT',data:obj(form)});toast('Correo del alumno actualizado por Enfermería');const a=await api(`/api/fichas/${form.dataset.id}`);$('#app').innerHTML=ficheDetail(a)}
  if(form.id==='edit-fiche-form'){
    const d=obj(form);
    d.antecedentes_familiares=[...form.querySelectorAll('[name=antecedentes_familiares]:checked')].map(x=>x.value);
    d.antecedentes_personales=[...form.querySelectorAll('[name=antecedentes_personales]:checked')].map(x=>x.value);
    d.autoriza_traslado=!!form.querySelector('[name=autoriza_traslado]')?.checked;
    d.validar_ahora=!!form.querySelector('[name=validar_ahora]')?.checked;
    const photoFile=form.querySelector('#foto-alumno-edit')?.files?.[0];
    if(photoFile){d.foto=await imageToData(photoFile)}
    await api(`/api/fichas/${form.dataset.id}`,{method:'PUT',data:d});
    toast('Expediente médico actualizado correctamente');
    S.editingFicheId=null;
    const a=await api(`/api/fichas/${form.dataset.id}`);
    $('#app').innerHTML=ficheDetail(a);
  }
  if(form.id==='bitacora-form'){
    const d=obj(form);
    d.firma_usuario=S.signatures.firma_usuario;
    d.firma_enfermeria=S.signatures.firma_enfermeria;
    if(!navigator.onLine){
      await OfflineDB.addQueue('/api/bitacora','POST',d,`Consulta de ${d.nombre||'paciente'}`);
      S.bitacoraDraft=null;
      delete S.draft.firma_usuario;
      delete S.draft.firma_enfermeria;
      S.bitacoraTab='list';
      toast('Atención guardada localmente (Modo Offline). Se sincronizará al volver la conexión.');
      await view('bitacora');
      return;
    }
    try{
      await api('/api/bitacora',{method:'POST',data:d});
      toast('Atención guardada en bitácora');
    }catch(err){
      if(!navigator.onLine || err.message?.includes('Modo sin conexión') || err.message?.includes('conectar al servidor')){
        await OfflineDB.addQueue('/api/bitacora','POST',d,`Consulta de ${d.nombre||'paciente'}`);
        toast('Sin conexión: Atención guardada localmente. Se sincronizará automáticamente.');
      } else throw err;
    }
    S.bitacoraDraft=null;
    delete S.draft.firma_usuario;
    delete S.draft.firma_enfermeria;
    S.bitacoraTab='list';
    await view('bitacora');
  }
  if(form.id==='referral-form'){
    const d=obj(form);
    d.consentimiento_informado=!!form.querySelector('[name=consentimiento_informado]').checked;
    d.firma_responsable=S.signatures.firma_responsable;
    d.firma_consentimiento=S.signatures.firma_consentimiento;
    if(!navigator.onLine){
      await OfflineDB.addQueue('/api/canalizaciones','POST',d,`Canalización de ${d.nombre_completo||'paciente'}`);
      S.referralDraft=null;
      delete S.draft.firma_responsable;
      delete S.draft.firma_consentimiento;
      S.referralTab='list';
      toast('Canalización guardada localmente (Modo Offline). Se sincronizará al volver la conexión.');
      await view('canalizaciones');
      return;
    }
    try{
      await api('/api/canalizaciones',{method:'POST',data:d});
      toast('Canalización guardada. Ya puedes generar PDF y enviarla.');
    }catch(err){
      if(!navigator.onLine || err.message?.includes('Modo sin conexión') || err.message?.includes('conectar al servidor')){
        await OfflineDB.addQueue('/api/canalizaciones','POST',d,`Canalización de ${d.nombre_completo||'paciente'}`);
        toast('Sin conexión: Canalización guardada localmente.');
      } else throw err;
    }
    S.referralDraft=null;
    delete S.draft.firma_responsable;
    delete S.draft.firma_consentimiento;
    S.referralTab='list';
    await view('canalizaciones');
  }
  if(form.id==='inventory-form'){
    const d=obj(form);
    d.cantidad_inicio=Number(d.cantidad_inicio);
    d.cantidad_fin=Number(d.cantidad_fin);
    d.stock_minimo=Number(d.stock_minimo||3);
    const id=form.dataset.id;
    if(!navigator.onLine){
      const ep = id ? `/api/inventario/${id}` : '/api/inventario';
      const m = id ? 'PUT' : 'POST';
      await OfflineDB.addQueue(ep, m, d, `Insumo ${d.medicamento_material}`);
      S.editInventory=null;
      toast('Insumo guardado localmente (Modo Offline).');
      await view('inventario');
      return;
    }
    try{
      if(id){await api(`/api/inventario/${id}`,{method:'PUT',data:d})}
      else{await api('/api/inventario',{method:'POST',data:d})}
      toast('Inventario guardado');
    }catch(err){
      if(!navigator.onLine || err.message?.includes('Modo sin conexión') || err.message?.includes('conectar al servidor')){
        const ep = id ? `/api/inventario/${id}` : '/api/inventario';
        const m = id ? 'PUT' : 'POST';
        await OfflineDB.addQueue(ep, m, d, `Insumo ${d.medicamento_material}`);
        toast('Insumo guardado localmente.');
      } else throw err;
    }
    S.editInventory=null;
    await view('inventario');
  }
  if(form.id==='contact-form'){
    const d=obj(form);
    const id=form.dataset.id;
    if(!navigator.onLine){
      const ep = id ? `/api/contactos/${id}` : '/api/contactos';
      const m = id ? 'PUT' : 'POST';
      await OfflineDB.addQueue(ep, m, {...d,activo:S.editContact?.activo??true}, `Contacto ${d.nombre}`);
      S.editContact=null;
      toast('Correo guardado localmente (Modo Offline).');
      await view('contactos');
      return;
    }
    try{
      if(id){await api(`/api/contactos/${id}`,{method:'PUT',data:{...d,activo:S.editContact?.activo??true}});toast('Correo actualizado en la base de datos')}
      else{await api('/api/contactos',{method:'POST',data:d});toast('Correo guardado en la base de datos')}
    }catch(err){
      if(!navigator.onLine || err.message?.includes('Modo sin conexión') || err.message?.includes('conectar al servidor')){
        const ep = id ? `/api/contactos/${id}` : '/api/contactos';
        const m = id ? 'PUT' : 'POST';
        await OfflineDB.addQueue(ep, m, {...d,activo:S.editContact?.activo??true}, `Contacto ${d.nombre}`);
        toast('Correo guardado localmente.');
      } else throw err;
    }
    S.editContact=null;
    await view('contactos');
  }
  if(form.id==='send-referral-form'){const ids=[...form.querySelectorAll('[name=contact_ids]:checked')].map(x=>Number(x.value));if(!ids.length)throw Error('Selecciona al menos un correo guardado.');if(!confirm(`¿Enviar documento médico a ${ids.length} destinatario(s) autorizado(s)?`))return;const r=await api(`/api/canalizaciones/${form.dataset.id}/enviar`,{method:'POST',data:{contact_ids:ids}});toast(r.ok?'Servidor de correo aceptó el mensaje.':'Algunos correos no pudieron enviarse',!r.ok);await view('canalizaciones')}
 }catch(err){parseErr(err)}finally{if(btn&&btn.isConnected)btn.disabled=false}
});

document.addEventListener('change', e => {
  if(e.target.id === 'select-estado-ficha'){
    const box = $('#box-observaciones-correccion');
    if(box) box.style.display = e.target.value === 'requiere_correccion' ? 'block' : 'none';
  }
});

// Dropzone drag & drop support
document.addEventListener('dragover',e=>{const dz=e.target.closest('#import-dropzone');if(dz){e.preventDefault();dz.classList.add('dragover')}});
document.addEventListener('dragleave',e=>{const dz=e.target.closest('#import-dropzone');if(dz){dz.classList.remove('dragover')}});
document.addEventListener('drop',async e=>{
  const dz=e.target.closest('#import-dropzone');
  if(dz){
    e.preventDefault();
    dz.classList.remove('dragover');
    const file=e.dataTransfer?.files?.[0];
    if(!file)return;
    S.importFile=file;
    const nameEl=$('#file-chosen-name');if(nameEl)nameEl.textContent=`Procesando: ${file.name}…`;
    try{
      const fd=new FormData();
      fd.append('file',file);
      const preview=await api('/api/estudiantes/importar/preview',{method:'POST',body:fd});
      S.importPreview=preview;
      $('#app').innerHTML=importarView(preview);
      toast(`Vista previa generada: ${preview.total} registros encontrados`);
    }catch(err){parseErr(err);if(nameEl)nameEl.textContent=''}
  }
});

(async()=>{
 if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'))navigator.serviceWorker.register('/service-worker.js').catch(()=>{});
 updateSyncBadge();
 try{
   const r=await api('/api/session');
   S.user=r.user;
   S.csrf=r.csrf;
   if(r.user) localStorage.setItem('samu-cached-user', JSON.stringify({user: r.user, csrf: r.csrf}));
 }catch{
   // Si estamos sin conexión, recuperar la última sesión válida para permitir trabajar en modo offline
   const cached = localStorage.getItem('samu-cached-user');
   if(cached){
     try {
       const parsed = JSON.parse(cached);
       S.user = parsed.user;
       S.csrf = parsed.csrf;
     } catch {}
   }
 }
 renderOfflineStatus();
 const path = location.pathname;
 if(path === '/alumno') view('alumno');
 else if(path === '/importar') { if(S.user) view('importar'); else view('login'); }
 else if(path === '/fichas') { if(S.user) view('fichas'); else view('login'); }
 else if(path === '/bitacora') { if(S.user) view('bitacora'); else view('login'); }
 else if(path === '/canalizaciones') { if(S.user) view('canalizaciones'); else view('login'); }
 else if(path === '/inventario') { if(S.user) view('inventario'); else view('login'); }
 else if(path === '/enfermeria' || path === '/dashboard') { if(S.user) view('dashboard'); else view('login'); }
 else if(path === '/login') { if(S.user) view('dashboard'); else view('login'); }
 else {
   if(S.user) view('dashboard'); else view('inicio');
 }
})();
