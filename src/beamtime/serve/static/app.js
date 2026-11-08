import{$ as Ke,A as en,Aa as it,B as me,Ba as Tt,C as He,D as tn,Da as vn,E as Qe,F as Ce,G as pe,Ga as bn,H as rn,I as Ct,J as et,Ja as yn,K as B,Ka as wn,L as X,La as kn,M as de,Ma as En,N as tt,Na as Tn,O as an,Oa as Mn,Pa as Nn,Q as De,R as Pe,Ra as Dn,T as ln,Ta as Pn,U as cn,Ua as Rn,V as k,Va as Ln,W as I,Wa as _n,X as nt,Xa as In,Y as Q,Ya as On,Z as z,Za as zn,_ as R,a as s,aa as W,ba as be,ca as O,d as U,da as ie,e as Be,ea as Ue,f as Te,fa as Fe,g as xt,ga as st,h as w,ha as ot,i as qt,ia as dn,j as oe,ja as je,k as Xt,ka as se,l as Yt,la as rt,m as Jt,n as Me,o as re,oa as un,p as S,pa as mn,q as Ze,qa as Ve,r as ae,ra as pn,s as Ne,sa as $n,t as xe,ta as fn,u as q,ua as D,v as F,va as at,w as Zt,wa as Et,xa as hn,y as N,ya as gn,z as Qt,za as Ge}from"./chunks/chunk-YZ3JESEH.js";import{a as Vt,b as Gt}from"./chunks/chunk-O2K4N3UR.js";import{B as sn,C as on,D as Y,E as St,G as ye,H as Se,I as Ee,J as j,K as We,R as xn,W as Cn,X as Sn,b as Ft,d as Wt,f as y,g as T,h as jt,i as L,j as ze,k as G,n as ke,o as M,p as ge,q as ve,v as nn,x as Ae}from"./chunks/chunk-FUNMOJMB.js";import"./chunks/chunk-VC46IEJQ.js";function Re(e,t){Me(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var Mt=["notes","timeline","groups","check","card","memory_show","status"];async function lt(e,t){let n=e.meta??{};await U("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Re(e.group,Mt)}async function Bn(e,t,n,o){await U("note_add",{group:e,type:t,description:n,body:o}),Re(e,Mt)}async function Hn(e,t){await U("memory_update",{group:e,body:t}),Re(e,["memory_show","status"])}async function An(e,t){let n=await U("proposal_show",{group:e}),o=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await U("proposal_set",{group:e,proposal:{...o,statement:t}}),Re(e,["groups","proposal_show","check","summary"])}async function Kn(e){await U("note_rm",{note:e.id}),Re(e.group,Mt)}async function Un(e,t,n){await U("name",{run:e,name:n}),Re(t,["card","runs","groups","summary","series"])}async function ct(e,t,n){let o=await U("view_text",{path:e,id:t,text:n});return Me(r=>["view","view_history"].includes(r.method)&&r.scope===e),o.id}async function Fn(e){await U("view_upgrade",{group:e}),Me(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Le=new ke(null);async function Wn(e,t){return await U("set",{key:e,value:t}),U("meta")}var ue=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),$e=(e,t=null,n=null,o=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...o?{metrics:o}:{}},scope:e}),Nt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),_e=e=>({method:"groups",params:{from:e,depth:0},scope:e}),jn=e=>({method:"check",params:{group:e},scope:e}),Vn=e=>({method:"proposal_show",params:{group:e},scope:e}),Ie=(e,t)=>({method:"card",params:{run:Ne(e,t)},scope:t}),Gn=(e,t)=>({method:"output",params:{run:Ne(e,t),tail:30},scope:t}),qn=(e,t)=>({method:"run_diff",params:{run:Ne(e,t)},scope:t}),qe=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),dt=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Xn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Yn=()=>({method:"status",params:{},scope:"."}),ut=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Xe(e){let t=je(e).value.main;for(let n of[$e(e,null,null,t),_e(e),qe(e),Nt(e,t)])xt(n);Te($e(e,null,null,t)).then(n=>{for(let o of Jn(n.view))xt(o)}).catch(()=>{})}function Jn(e){return e?[...Zs.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(Jn)]:[]}var Zs=new Set(["line","custom"]),Zn=e=>({method:"view_history",params:{group:e},scope:e});var pt="/static/favicon.svg",mt=null;async function Qs(){if(mt)return mt;let e=new Image;e.src=pt,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let o=n.getContext("2d");if(!o)return pt;let r=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return r?(o.drawImage(e,0,0,t,t),o.beginPath(),o.arc(t-6,t-6,6,0,Math.PI*2),o.fillStyle=r,o.fill(),mt=n.toDataURL("image/png"),mt):pt}function eo(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=pt;return}Qs().then(n=>{t.type="image/png",t.href=n})}}function Ye(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,eo(t>0)},[e,t])}function Qn(e){let t=re(e.split("/").pop()??""),n=w(t?null:_e(e)),o=w(t?Ie(e.split("/").pop()??"",e):null),r=t?o.data?.run.name??o.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,a=t?o.data?.run.status==="running"?1:0:R(n.data)[0]?.running??0;Ye(r,a)}var ee=new ke(ge("sidebar",!0)),te=new ke(null),fe=new ke(!1),he=new ke(null);ee.subscribe(e=>ve("sidebar",e));var es=ge("visit",Date.now());ve("visit",Date.now());function ts(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var $t=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var to=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function ft(e){he.set(e),Qe.set(e.theme),Ae.set(e.colormaps),e.settings?.theme_mode&&pe.set(e.settings.theme_mode),Ct()}var ns=0;async function Dt(e,t){let n=++ns;e==="theme_mode"&&(pe.set(t),Ct());let o=await Wn(e,t);n===ns&&ft(o)}function ss(){let e=M(pe),t=de(),n=M(he),[o,r]=y(null);Ye("Settings");let a=(c,d)=>{r(null),Dt(c,d).catch(g=>r(g.message))},l=n?.settings??{},i=(c,d,g)=>s`
    <label class="field-label small" for=${`setting-${c}`}>${d}</label>
    <span class="input body">
      <select id=${`setting-${c}`} value=${l[c]} onChange=${m=>a(c,m.target.value)}>
        ${g.map(m=>s`<option value=${m}>${m}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${O} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${o?s`<${z} kind="error">${o}<//>`:null}
    <//>
    <${O} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${to.map(([c,d,g])=>s`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>a("theme_mode",c)}>
            <${k} name=${d} size=${15} />${g}</button>`)}
        </div>
        ${i("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(c=>s`<${z} kind="warning">${c}<//>`)}
    <//>
    <${O} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${ot} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${c=>a("figure_style",c)} />`:s`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${O} label="keyboard">
      <table class="kv">${$t.map(([c,d])=>s`<tr><td><kbd class="small">${c}</kbd></td><td>${d}</td></tr>`)}</table>
    <//>
    <${O} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(c=>s`
          <tr><td class="muted">${c.name}</td><td><code class="code">${c.logdir}</code> (${c.kind}, ${c.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var os={system:"light",light:"dark",dark:"system"},no={system:"monitor",light:"sun",dark:"moon"};function rs(){let e=M(he),t=M(pe),n=M(ee);return s`<header class="topbar">
    <${W} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>ee.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>te.set("")} aria-label="Search (⌘K)">
      <${k} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${so} />
      <${W} icon=${no[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${os[t]})`}
        onClick=${()=>{Dt("theme_mode",os[t])}} />
      <a class="icon-button" href=${Ze(F.value.page==="group"?F.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${k} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${k} name="settings" size=${16} /></a>
    </div>
  </header>`}function so(){let t=(w(ue()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${S(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${k} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${k} name="server" size=${15} /> local</span>`}function oo(e){let[t,n]=y(Date.now());return T(()=>{let o=setInterval(()=>n(Date.now()),e);return()=>clearInterval(o)},[e]),t}function ro(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function as(){let e=M(Xt),t=M(oe),n=M(Yt),o=M(F),r=oo(5e3),a=w(Yn()).data,l=R(w(ut()).data),i=M(he),c=a?.daemon,d=a?.runs?.running??0,g=l.filter(E=>E["run.status"]==="failed"&&ro(E["run.ended_at"])>es).length,m=a?.meta?.freshness,[p,$,v]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${j(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${v}><span class=${`live-dot ${p}`}></span>${$}</span>
    ${d?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>te.set("running")}>
          <${k} name="circle-dot" size=${14} class="tone-accent" />${d} running</button>`:null}
    ${g?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>te.set("failed")}>
          <${k} name="circle-x" size=${14} />${g} failed since your last visit</button>`:null}
    ${m?.behind?s`<span class="status-item warn-text" data-tip=${m.text}><${k} name="hourglass" size=${14} />${m.behind} runs behind</span>`:null}
    ${m?.damaged?.length?s`<span class="status-item warn-text" data-tip=${m.damaged.join(`
`)}><${k} name="triangle-alert" size=${14} />${m.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${o.page==="group"&&o.run?s`<span class="status-item"><${k} name="activity" size=${14} />1 run selected</span>`:null}
    <${W} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>oe.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var is=null;function ht(e){let t=L(null),[n,o]=y(null),[r,a]=y(!1),[l,i]=y(!1);T(()=>{let m=!0;return is??=import("./chunks/md-SW3VT2BQ.js"),is.then(p=>p.render(e.text??"")).then(p=>m&&o(p)),()=>{m=!1}},[e.text]),jt(()=>{let m=t.current;if(!m||!e.clamp)return;let p=()=>i(m.scrollHeight>m.clientHeight+2),$=new ResizeObserver(p);return $.observe(m),()=>$.disconnect()},[e.clamp,n]);let c=e.clamp&&!r,d=`md${c?" clamped":""}`,g=c?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${d} ref=${t} style=${g}>
          ${(e.text??"").split(/\n{2,}/).map(m=>s`<p>${m}</p>`)}
        </div>`:s`<div class=${d} ref=${t} style=${g} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link small more" onClick=${()=>a(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function we(e){let[t,n]=y(!!e.startEditing),[o,r]=y(e.value),[a,l]=y(null),[i,c]=y(null),d=L(null),g=L(!1);T(()=>l(null),[e.value]),T(()=>{!t||!d.current||(d.current.focus(),e.startEditing?d.current.select():d.current.setSelectionRange(d.current.value.length,d.current.value.length))},[t]);let[m,p]=y(!1),$=e.locked??void 0,v=f=>{if(!f.target.closest("a, button, input, summary")){if($)return p(!0);f.preventDefault(),r(a??e.value),c(null),g.current=!1,n(!0)}},E=()=>{g.current=!0,n(!1),c(null),e.onCancel?.()},h=async()=>{if(g.current)return;g.current=!0;let f=e.multiline?o.trim():o.replace(/\s*\n\s*/g," ").trim();if(f===e.value.trim()||!f&&!e.multiline)return E();n(!1),l(f);try{await e.onSave(f)}catch(b){l(null),r(f),c(b.message),g.current=!1,n(!0)}},x=f=>{if(f.key==="Escape")return f.preventDefault(),f.stopPropagation(),E();f.key!=="Enter"||f.isComposing||f.keyCode===229||(!e.multiline||f.metaKey||f.ctrlKey)&&(f.preventDefault(),h())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${d} class="edit-field" value=${o} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,o.split(`
`).length+1)):1}
        onInput=${f=>r(f.target.value)} onKeyDown=${x} onBlur=${h}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let u=a??e.value;return s`<div class=${`editable${$?" locked":""}${a!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${$?`${e.label}: ${$}`:`Edit ${e.label}`}
      data-tip=${$} onClick=${v} onBlur=${()=>p(!1)}
      onKeyDown=${f=>f.key==="Enter"&&f.target===f.currentTarget&&v(f)}>
    ${u.trim()?e.render?e.render(u):u:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${m&&$?s`<span class="edit-hint small locked-why" role="status"><${k} name="lock" size=${14} /> ${$}</span>`:null}
  </div>`}function Pt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function ls({node:e}){let t=X("proposal"),n=X("check"),o=t.data,r=n.data;if(!o)return s`<${Q} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let a=o.proposal??{},l=(o.versions??[]).filter(c=>c.version!==o.version),i=!e.props.of||e.props.of===".";return s`<${Q} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${a.statement}</p>`}
    ${a.rationale?s`<p class="rationale prose">${a.rationale}</p>`:null}
    <${gn} predictions=${r?.predictions} />
    ${l.length?s`<${Fe} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>s`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function cs({node:e}){let t=X("main"),n=e.data?.main.params.group??".",o=t.data?.chain??[],r=o.find(i=>i.group===n)??null,a=o.filter(i=>i.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${Ke} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${s`<${I} spec=${{icon:"circle-help",tone:"muted",label:io}} />`}>
    <${we} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${ht} text=${i} />`} onSave=${i=>Hn(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=ao)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${a.length?s`<p class="memory-meta small">Memory above this group: ${a.map((i,c)=>s`${c?", ":""}<a href=${S(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var ao=5,io="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",lo="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function ds({node:e}){let t=X("main"),n=e.data?.main.params.from??".",o=R(t.data).filter(r=>r.path!==n);return s`<${Q} title=${e.props.title} count=${t.data?String(o.length):void 0} result=${t}>
    ${t.data&&!o.length?s`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${o.map(r=>{let[a,l]=Pt(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${S(r.path)}
            onPointerEnter=${()=>Xe(r.path)} onFocus=${()=>Xe(r.path)}>
          <${I} spec=${D("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${D("research",r.status).tone}`}>${D("research",r.status).label}</span>`:null}
            ${r.check?s`<${I} spec=${D("result",r.check)} word />`:null}
            ${r.verdict?s`<${I} spec=${D("verdict",r.verdict)} />`:null}
            ${a?s`<span data-tip=${l}>${a}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${I} spec=${D("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${k} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function us({node:e}){let t=X("main"),n=e.data?.main.params.from??".",[o,r]=y(!1),a=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),l=t.data?.meta?.matched??a.length;return s`<${Ke} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${I} spec=${{icon:"circle-help",tone:"muted",label:lo}} />
        ${s`<${W} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${o?s`<${mo} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!a.length&&!o?s`<p class="muted small">No notes yet.</p>`:null}
      ${a.map(i=>s`<${gt} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${ms} call=${e.data.main} before=${a[a.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var co=20;function ms(e){let[t,n]=y(!1),o=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:co}}:null,r=w(o);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let a=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${a.map(l=>s`<${gt} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${ms} call=${e.call} before=${a[a.length-1]?.id} scope=${e.scope} />`:null}`}var uo=["observation","decision","idea","question","theory"];function ps(e){return(e?.note_types??uo).filter(t=>t!=="verdict")}function mo(e){let t=ps(M(he)),[n,o]=y("observation"),[r,a]=y(""),[l,i]=y(""),[c,d]=y(null),[g,m]=y(!1),p=async v=>{if(v.preventDefault(),!r.trim())return d("give the note a title");m(!0);try{await Bn(e.group,n,r.trim(),l.trim()),e.onDone()}catch(E){d(E.message),m(!1)}};return s`<form class="note new-note" onSubmit=${p} onKeyDown=${v=>{v.key==="Escape"&&e.onDone(),v.key==="Enter"&&(v.metaKey||v.ctrlKey)&&p(v)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${v=>o(v.target.value)}>
        ${t.map(v=>s`<option value=${v}>${v}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${r} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${v=>a(v.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${l} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${v=>i(v.target.value)}></textarea></span>
    <div class="save-actions">
      <${ie} type="submit" icon=${g?"hourglass":"plus"} disabled=${g}>${g?"Adding\u2026":"Add note"}<//>
      <${ie} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${c?s`<span class="bad-text small">${c}</span>`:null}
    </div>
  </form>`}function po({note:e}){let t=ps(M(he)).filter(n=>n!==e.type);return e.type==="verdict"?s`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${k} name=${D("note","verdict").icon} size=${15} /></span>`:s`<${st} icon=${D("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>s`<button type="button" key=${n} onClick=${()=>lt(e,{type:n})}>
        <${k} name=${D("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function gt(e){let t=e.note,[n,o]=y(!!e.open),[r,a]=y(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${d=>!d.target.closest(".editable, a, .note-delete, .popover-wrap")&&o(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${k} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${po} note=${t} />
      <${we} value=${t.description} label="the note's title" class="note-title heading" render=${fo}
        onSave=${d=>lt(t,{description:d})} />
      ${t.overall?s`<${I} spec=${D("verdict",t.overall)} />`:null}
      ${t.state?s`<${be} tone="warn">${t.state}<//>`:null}
      ${l?s`<a class="note-group small" href=${S(l)} data-tip="from this group">${$o(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${j(i)}</span>
      ${s`<${W} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${d=>{d.stopPropagation(),a(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ie} icon="trash" kind="danger" onClick=${()=>{Kn(t)}}>Delete<//>
          <${ie} icon="x" kind="quiet" onClick=${()=>a(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${we} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${d=>s`<${ht} text=${d} />`}
          onSave=${d=>lt(t,{body:d})} />`:null}
  </article>`}function $o(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,o=n.split("/").pop()??n;return re(o)?o.slice(-8):n}function $s({node:e}){let t=X("main"),n=t.data?.lines??[],o=t.data?.meta??{},r=s`<${k} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${o.total_lines??n.length} lines${(o.shown??0)<(o.total_lines??0)?`, last ${o.shown}`:""}`:""}</span>`;return s`<${Q} result=${t}>
    <${Fe} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function fs({node:e}){let t=G(B);return s`<${Q} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${we} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Le.value===e.id} onCancel=${()=>Le.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${ht} text=${n} />`}
      onSave=${n=>(Le.set(null),ct(t.path,e.id,n))} />
  <//>`}function hs({node:e}){return s`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function fo(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let o=n.slice(2,-2),[r]=o.split(/[#@]/),a=r.split("/").pop()??"";return s`<a href=${re(a)?ae(a):S(r)}>${o}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function ho(e,t){let n=/^(?:ssh|https?|git):\/\/(?:[^@/]*@)?([^/:]+)(?::\d+)?\/(.+?)(?:\.git)?\/?$/.exec(e??""),o=/^(?:[^@/]+@)?([^/:]+):(?!\/)(.+?)(?:\.git)?\/?$/.exec(e??""),[,r,a]=n??o??[];return!r||!a?null:r==="github.com"?{host:"GitHub",url:`https://github.com/${a}/commit/${t}`}:r==="gitlab.com"||r.startsWith("gitlab.")?{host:"GitLab",url:`https://${r}/${a}/-/commit/${t}`}:null}function vt(e){let{git:t,copied_from:n}=e.run,o=[];return t?.commit&&o.push(["code",s`<${go} git=${t} />`]),n&&o.push(["copied from",s`<a href=${ae(n.id)} data-tip=${`${n.id}, ${n.at}`}>${n.path??n.id}</a>`]),e.checkpoints?.length&&o.push(["checkpoints",s`${e.checkpoints.map(r=>s`<${vo} key=${r.name} ck=${r} />`)}`]),o}function go({git:e}){let t=ho(e.remote,e.commit);return s`<span>${e.commit.slice(0,10)}${e.branch?s` on ${e.branch}`:null}
    ${e.dirty?s` <${be} tone="warn" tip="Uncommitted changes when the run started">dirty<//>`:null}
    ${t?s` · <a href=${t.url} target="_blank" rel="noopener noreferrer">${t.host}</a>`:null}</span>`}function vo({ck:e}){let t=()=>{navigator.clipboard?.writeText(e.location)};return s`<div class="checkpoint">
    <span class=${e.exists?"":"muted"} data-tip=${e.location??void 0}>${e.name}</span>
    ${e.exists?null:s`<${be} tone="warn" tip=${e.location??void 0}>missing<//> <span class="muted">${bo(e)}</span>`}
    ${e.location?s`<${W} icon="copy" label=${`Copy the path of ${e.name}`} onClick=${t} />`:null}
  </div>`}function bo(e){return e.location?e.via==="origin"?"not found where the source run kept it":"not found at its recorded location":"no location recorded"}function bt({run:e,scope:t}){let[n,o]=y(!1),r=w(n?qn(e,t):null);return s`<${Fe} summary="Uncommitted changes" onToggle=${o}>
    ${r.error?s`<p class="muted small">${r.error}</p>`:null}
    ${r.data?s`<pre class="log code diff">${String(r.data.text).split(`
`).map(a=>s`<span class=${yo(a)}>${a}\n</span>`)}</pre>`:n&&!r.error?s`<div class="skeleton late" style="block-size: 80px"></div>`:null}
  <//>`}function yo(e){return e.startsWith("+++")||e.startsWith("---")||e.startsWith("@@")?"muted":e.startsWith("+")?"tone-good":e.startsWith("-")?"tone-bad":""}function gs(e){let t=()=>N(S(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${k} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${W} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${wo} id=${e.run} scope=${e.path} />`:s`<${ko} path=${e.path} />`}
  </aside>`}function wo({id:e,scope:t}){let n=w(Ie(e,t)).data,o=w(Gn(e,t)).data,r=w(qe(t)).data,a=w({method:"keys",params:{from:t},scope:t}).data,l=de(),i=ze(()=>tt(R(r).map(p=>p["run.id"]),l).get(e),[r,l,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let c=n.run,d=Object.entries(n.metrics??{}),g=nn(i,l),m=vt(n);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${g.class} style=${g.style}></span>
      <a href=${ae(e)}>${c.name}</a></h3>
    <p class="facts small">
      <${I} spec=${at(c.status,c.exit)} word />
      <span><b>${Se(c.steps)}</b> steps</span>
      <span><b>${Ee(c.duration_s)}</b></span>
      <span data-tip=${c.created_at}>${j(c.created_at)}</span>
    </p>
    ${c.error?s`<pre class="log code bad-text">${c.error}</pre>`:null}
    ${m.length?s`<table class="kv small">${m.map(([p,$])=>s`<tr><td class="muted">${p}</td><td>${$}</td></tr>`)}</table>`:null}
    ${c.git?.dirty?s`<${bt} run=${c.id} scope=${t} />`:null}
    <h4 class="small">Config</h4>
    <${it} config=${n.config??{}} varying=${Ge(a)} />
    ${d.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${d.map(([p,$])=>s`<tr><td>${p}</td><td class="num"><b>${Y($.last)}</b></td>
              <td class="num">${Y($.min)}</td><td class="num">${Y($.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(p=>s`<p class="small"><${I} spec=${D("note",p.type)} /> ${p.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(p=>s`<div class="event small"><span class="muted num">${p.t?.slice(5,16).replace("T"," ")}</span>
        <${k} name=${Et(p.type)} size=${14} /><span>${p.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(o?.lines??[]).join(`
`)}</pre>
  </div>`}function ko({path:e}){let t=w(dt(e)).data,n=w(Xn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(o=>!String(o.state??"").startsWith("superseded")).map(o=>s`<${gt} key=${o.id} note=${o} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(o=>s`<div class="event small"><span class="muted num">${o.t?.slice(5,16).replace("T"," ")}</span>
        <${k} name=${o.kind==="note"?"file-text":Et(o.type)} size=${14} />
        <span>${o.run?s`<a href=${ae(o.run)}>${o.run.slice(-8)}</a> `:null}${o.description??o.type}</span></div>`)}
  </div>`}function yt(e,t){let n=w(e),o=L(null);return n.status!=="loading"&&(o.current={scope:t,result:n}),n.status==="loading"&&o.current?.scope===t?o.current.result:n}var Rt=null;function vs(e){Rt?.();let t=document.querySelector(".main");if(!e||!t)return;let n=e.getBoundingClientRect().top,o=new ResizeObserver(()=>{e.isConnected&&(t.scrollTop+=e.getBoundingClientRect().top-n)});for(let i of t.children)o.observe(i);let r=["wheel","touchmove","keydown","pointerdown"],a=()=>{o.disconnect(),clearTimeout(l);for(let i of r)removeEventListener(i,a);Rt=null},l=setTimeout(a,5e3);for(let i of r)addEventListener(i,a,{passive:!0});Rt=a}var Lt=["failed","killed","lost"];function _t(e){let t=xe(e.path),n=t==="."?e.path:e.path.slice(t.length+1),o=q(e.path)?[]:n.split("/"),r=o.length&&re(o[o.length-1])?o[o.length-1]:null,a=o.slice(0,-1),l=i=>[...t==="."?[]:[t],...a.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${o.length?s`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${a.map((i,c)=>s`<span>/</span><a href=${S(l(c))}>${i}</a>`)}
    </nav>
    ${r?s`<${So} id=${r} scope=${e.path} />`:s`<${xo} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function xo({path:e}){let t=R(w(_e(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let o=Object.entries(w({method:"keys",params:{from:e},scope:e}).data?.codes??{}),r=Lt.reduce((a,l)=>a+(t[l]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${I} spec=${D("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${r?s`<span class="tone-bad" data-tip=${Lt.filter(a=>t[a]).map(a=>`${t[a]} ${a}`).join(", ")}>
            <${k} name="circle-x" size=${15} /> <b>${r}</b> ${r===1?Lt.find(a=>t[a]):"ended early"}</span>`:null}
      ${o.length?s`<span data-tip=${o.map(([a,l])=>`${a}: ${l} run${l===1?"":"s"}`).join(", ")}>
            <${k} name="git-commit" size=${15} /> <b>${o.length}</b> code versions</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${ys} path=${e} />
    </p>`}function bs({path:e}){let t=R(w(_e(e)).data)[0]??null,n=w(t?.proposal?jn(e):null).data,o=w(t?.proposal?Vn(e):null).data;if(!t?.proposal)return null;let r=o?.proposal?.rationale,a=o?.versions?.find(c=>c.version===o.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,i]=Pt(n?.progress?.text??t.progress);return s`<${O} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${we} value=${t.proposal} label="the proposal's statement" locked=${o?a:"Loading the proposal\u2026"}
          render=${c=>s`<span data-tip=${a?void 0:r}>${c}</span>`}
          onSave=${c=>An(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let d=D("result",c.result),g=hn(c),m=g?`${d.label}: ${g}`:d.label;return s`<span class=${`check small tone-${d.tone}`} key=${c.name} data-tip=${m}
              aria-label=${`${c.name}: ${m}`} tabindex="0"><${k} name=${d.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${Co} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Co(e){let t=w(e.verdict?dt(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=D("verdict",e.verdict),o=(t?.entries??[]).find(a=>a.type==="verdict"&&(a.group??e.path)===e.path),r=o?ye(o.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${k} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${o?s`<span class="small muted" data-tip=${r}>verdict${o.meta?.author?` by ${o.meta.author}`:""}${r?` \xB7 ${j(r)}`:""}</span>`:null}
  </p>`}function So({id:e,scope:t}){let n=w(Ie(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let o=n.run,r=()=>{navigator.clipboard?.writeText(o.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${we} value=${o.name??o.id} label="the run's name" class="title-edit"
        onSave=${a=>Un(o.id,t,a.trim())} />
      <${I} spec=${at(o.status,o.exit)} word /></h1>
    ${o.error?s`<p class="bad-text" data-tip=${o.error}>${o.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${Se(o.steps)}</b> steps</span>
      <span><b>${Ee(o.duration_s)}</b></span>
      ${n.progress?s`<${Eo} run=${o} progress=${n.progress} />`:null}
      <span data-tip=${o.created_at}>${j(o.created_at)}</span>
      <${ys} path=${t} />
      <${W} icon="copy" label=${`Copy the run id ${o.id}`} onClick=${r} />
      <${st} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${[...To(o),...vt(n)].map(([a,l])=>s`<tr><td class="muted">${a}</td><td>${l}</td></tr>`)}</table>
        ${o.git?.dirty?s`<${bt} run=${o.id} scope=${t} />`:null}
        <div class="menu-list">
          <button type="button" onClick=${()=>N(S(t,{run:o.id}),{replace:!0})}>
            <${k} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${k} name="copy" size=${15} /> Copy the run id</button>
          ${o.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(o.git.commit)}>
            <${k} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(a=>{let l=D("result",a.check);return s`<a class=${`check small tone-${l.tone}`} href=${S(a.group)} data-tip=${a.statement}>
              <${k} name=${l.icon} size=${14} />${a.group==="."?"own proposal":a.group}
              ${a.verdict?s`<${I} spec=${D("verdict",a.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Eo({run:e,progress:t}){let{epoch:n,total:o,fraction:r,steps_per_epoch:a}=t,l=e.status==="running"&&r!==null&&a&&e.steps_per_s?Ee((1-r)*o*a/e.steps_per_s):null;return s`<span>epoch <b>${n}</b>${o?` of ${o}`:""}${r===null?"":` \xB7 ${Math.round(r*100)} % through`}${l?` \xB7 about ${l} left`:""}</span>`}function ys({path:e}){let t=se(e).main,n=yt(Nt(e,t),e).data?.summary;if(!n)return null;let o=Object.entries(n.config??{}).map(([l,i])=>`${We(l)} ${Y(i)}`).join(", "),r=re(e.split("/").pop()??""),a=`${n.stat} of ${n.metric} over ${r?"the run":"all runs"}${o?` (${o})`:""}`;return s`<span data-tip=${a}>
    best <b>${n.label??We(`metric.${n.metric}.${n.stat}`)} ${Y(n.value)}</b>
    ${r?null:s` · <a href=${ae(n.run)}>${n.name}</a>`}
  </span>`}function To(e){return[["id",e.id],["host",e.host],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,o])=>[n,String(o)])}var It=80;function ws({node:e}){let t=X("main"),n=X(e.data?.keys?"keys":""),o=e.props.mode==="run",r=e.props.title??(o?"Config":"Hyperparameters");return s`<${Ke} id=${`config:${e.id}`} title=${r} open=${e.props.open} result=${t}>
    ${t.data?o?s`<${it} config=${t.data.config} varying=${Ge(n.data)} />`:s`<${Mo} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function Mo({rows:e}){let t=new Set(Ge({config:{rows:e}})),n=e.filter(([o])=>t.has(o.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([o,,r])=>{let a=Array.isArray(r)?r.map(Y).join(", "):`${Y(r.min)} \u2026 ${Y(r.max)} \xB7 ${r.distinct} values`;return s`<tr><td data-tip=${o}>${o.replace(/^config\./,"")}</td>
      <td data-tip=${a.length>It?a:void 0}>${a.length>It?`${a.slice(0,It-1)}\u2026`:a}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var ks=15e3;function xs({node:e}){let t=G(B),n=de(),[o,r]=an(),a=e.props.code,l=w(r&&a?{method:"code",params:a,scope:null}:null),[i,c]=y(null),[d,g]=y(120),[m,p]=y({error:null,warnings:[]}),$=x=>{me&&console.error(`[block ${e.id}] ${x}`),p(u=>({...u,error:x}))},v=L(()=>{});T(()=>{if(!i)return;p(b=>b.own?{...b,own:!1}:b);let x=!0;Be.n++;let u=()=>{x&&Be.n--,x=!1};v.current=u;let f=setTimeout(()=>{x&&$(`no first render within ${ks/1e3} s`),u()},ks);return()=>{clearTimeout(f),u()}},[i]),T(()=>{let x=i?.contentWindow;if(!x||l.status!=="ready")return;let u=P=>x.postMessage(P,"*"),f=new Map,b=new kn,K=P=>{if(P.source!==x)return;let C=P.data;switch(C.type){case"hello":u({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:rn.value,pair:Qe.value,colormaps:Ae.value,prefs:je(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics,expanded:e.props.expanded?vn():null}});break;case"sub":if(!bn.has(C.call.method)){u({type:"result",id:C.id,result:{status:"error",data:null,error:`${C.call.method} is not available in a custom block`,refreshing:!1}});break}f.get(C.id)?.(),f.set(C.id,qt(C.call,ne=>u({type:"result",id:C.id,result:ne})));break;case"unsub":f.get(C.id)?.(),f.delete(C.id);break;case"navigate":C.url.startsWith("/")&&N(C.url);break;case"height":b.accept(performance.now())?g(Math.max(40,C.height)):H("its height keeps changing, so it is fixed at its last height");break;case"chrome":p(ne=>({...ne,own:C.own}));break;case"ready":p(ne=>({...ne,blank:C.blank,overflow:C.overflow})),v.current();break;case"warn":H(C.message);break;case"hover":Ce.set(C.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(C.prefs)&&A.set(C.prefs);break;case"download":case"snapshot":C.href?yn(C.href,C.name)?performance.now()-V>1e3&&(V=performance.now(),Pe().download(C.href,C.name)):H(`a download of ${C.name} was refused: only PNG, SVG and CSV files`):H("it draws no SVG or canvas to download");break;case"figure":Pe().figure(C.spec,C.name).catch(ne=>H(`the PDF failed: ${ne.message}`));break;case"expand":wn(C.node)&&Pe().expand(C.node,t);break;case"expand-block":e.props.expanded||Pe().expand(e,t);break;case"close":e.props.expanded&&De.set(null);break;case"error":$(C.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,E)),v.current();break;default:break}},H=P=>{me&&console.warn(`[block ${e.id}] ${P}`),p(C=>C.warnings.includes(P)?C:{...C,warnings:[...C.warnings,P]})},V=-1/0,A=je(t.path),Z=Ce.subscribe(P=>u({type:"hover",run:P})),_=A.subscribe(P=>u({type:"prefs",prefs:P}));return addEventListener("message",K),u({type:"ping"}),()=>{Z(),_(),removeEventListener("message",K);for(let P of f.values())P()}},[l.status,l.data?.code,i]),T(()=>{let x={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(x,"*")},[t.names,t.colors,t.metrics,i]),T(()=>Ae.subscribe(x=>i?.contentWindow?.postMessage({type:"colormaps",colormaps:x},"*")),[i]),T(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let E=typeof a=="object"?a.path??a.block:String(a??"");ln(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let h=r&&l.status==="ready"&&!m.error;return s`<div ref=${o} class="custom-block">
    ${m.own?null:s`<div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${h?s`<span class="chart-tools">
            <${W} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${W} icon="x" label="Close (Esc)" onClick=${()=>De.set(null)} />`:s`<${W} icon="maximize" label="Expand" onClick=${()=>Pe().expand(e,t)} />`}
          </span>`:null}
    </div>`}
    <${Q} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${m.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${E})</span>
            <pre class="code">${m.error}</pre>
          </div>`:null}
      ${m.warnings.map(x=>s`<${z} kind="warning">${x}<//>`)}
      ${h?s`<div class="custom-frame" data-frame-blank=${m.blank?"1":void 0} data-frame-overflow=${m.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${No()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${d}px`} />
          </div>`:null}
    <//>
  </div>`}function No(){if(!!1)return{src:Vt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function Cs({node:e}){let t=X("main"),n=G(B),o=t.data?.entries??[];return s`<${Q} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!o.length?s`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${o.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Gt(Ne(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${He?"eager":"lazy"} />
          <figcaption class="small">step ${Se(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function Ss({node:e}){let t=X("main"),n=t.data?.entries??[];return s`<${Q} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${z}>No text logged.<//>`:null}
    ${n.map(o=>s`<div class="text-entry" key=${`${o.run}/${o.step}`}>
        <div class="muted small">step ${Se(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</div>
        <pre class="code">${o.text??""}</pre>
      </div>`)}
  <//>`}function Es({node:e}){let n=`section.${G(B).path}:${e.id}`,[o,r]=y(()=>He||ge(n,e.props.open!==!1)),a=()=>{ve(n,!o),r(!o)},l=s`${(e.children??[]).map(d=>s`<${ce} key=${d.id} node=${d} />`)}`,i=G(nt);if(!e.props.title)return s`<div class="stack">${l}</div>`;let c=i===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${o} aria-label=${c?`${o?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${c?`${o?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${a}>
      <${k} name=${o?"chevron-down":"chevron-right"} size=${16} />${c?null:e.props.title}
    </button>
    ${o?s`<div class="stack">${l}</div>`:null}
  </div>`}function Ts({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${ce} key=${n.id} node=${n} />`)}
  </div>`}function zt({node:e,after:t}){let n=G(B),o=se(n.path),r=e.props.min_width??320,a=e.props.columns,l=a?`grid-template-columns: repeat(${a}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${r}px, 100%), 1fr))`,i=e.children??[],c=i.filter(m=>o.removed.includes(m.id)).map(m=>m.id),d=fn(i.filter(m=>!c.includes(m.id)),o.order[e.id]),g=(m,p)=>{let $=d.map(v=>v.id).filter(v=>v!==m);if($.splice($.indexOf(p),0,m),pn(n.path,e.id,$),e.id===dn){let v=h=>i.find(x=>x.id===h)?.data?.main?.params?.y?.[0],E=$.map(h=>n.pins.find(x=>x.y===v(h))).filter(h=>!!h);mn(n.path,[...E,...n.pins.filter(h=>!E.includes(h))])}};return s`<div class="grid" style=${l}>
    ${d.map(m=>s`<${Do} key=${m.id} node=${m} path=${n.path} span=${o.spans[m.id]??m.props.span??1}
      columns=${a} onDrop=${p=>p!==m.id&&g(p,m.id)} />`)}
    ${t??null}
    ${c.length?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ve(n.path,c)}>${c.length} hidden · show</button></div>`:null}
  </div>`}var Ot=[1,2,"full"];function Do(e){let[t,n]=y(!1),o=Ot[(Ot.indexOf(e.span)+1)%Ot.length],r=a=>a==="full"?"full width":`${a} column${a===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${a=>{a.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${a=>{a.preventDefault(),n(!1),e.onDrop(a.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${a=>a.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${k} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(o)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>$n(e.path,e.node.id,o)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ce} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Bt({root:e}){let t=G(B),n=se(t.path),o=w({method:"keys",params:{from:t.path},scope:t.path}).data,r=e.props.template;if(!r||!1)return null;let a=new Set(n.removed),l=new Set([...t.charted].filter(([$])=>!a.has($)).flatMap(([,$])=>$)),i=n.added.filter($=>!l.has($)).map($=>({block:"line",id:`added-${$}`,props:{y:$},data:{main:{...r,params:{...r.params,y:[$]}}}})),c=new Set([...l,...i.filter($=>!a.has($.id)).map($=>$.props.y)]),d=(o?.metrics?.rows??[]).map($=>$[0]).filter($=>!c.has($));if(!o||!(d.length||i.length))return null;let g=$=>[...t.charted].find(([v,E])=>a.has(v)&&E.includes($))?.[0]??i.find(v=>a.has(v.id)&&v.props.y===$)?.id,m=$=>{let v=g($);v?Ve(t.path,[v]):rt(t.path,E=>({added:[...E.added,$]}))},p=d.length?s`<div class="add-chart">
        <span class="add-chart-label"><${k} name="plus" size=${16} /> Add a chart</span>
        <${ot} single options=${d} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([$])=>m($)} />
      </div>`:null;return s`<${O}><${zt} node=${{block:"grid",id:"added",props:{},children:i}} after=${p} /><//>`}function Ms({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[o,r]=y(()=>t.find(i=>i.id===n())?.id??t[0]?.id),a=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},l=t.find(i=>i.id===o)??t[0];return He?s`<div class="stack">${t.map(i=>s`<${ce} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===l?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>a(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(i=>s`<${ce} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}function Ns({node:e}){let t=X("main"),n=G(B),o=M(Ce),r=e.props,a=xn(t.data,r.rows,r.columns,r.lower??{},r.expected??[]),l=F.value.page==="group"?F.value.run:null,i=r.baseline===null||r.baseline===void 0?null:a.find(d=>d.label===String(r.baseline)),c=d=>N(S(n.path,{run:d}),{replace:l!==null});return s`<${Q} title=${r.title} caption=${r.caption} numbered result=${t}>
    ${t.data?s`<div class="table-wrap"><table class="runs scorecard">
          <thead><tr class="small">
            <th data-tip=${r.rows}>${We(r.rows)}</th>
            ${r.columns.map(d=>s`<th class="num" data-tip=${d}>${Mn(d,n.metrics)}</th>`)}
          </tr></thead>
          <tbody onPointerLeave=${()=>Ce.set(null)}>
            ${a.map(d=>{let g=`${d.runs.includes(l??"")?"selected":""}${d.runs.includes(o??"")?" hovered":""}${d.queued?" queued":""}`;return s`<tr key=${d.label} class=${g} data-tip=${d.runs.length?`${d.runs.length} run${d.runs.length>1?"s":""}`:void 0}
                  onClick=${d.runs.length?()=>c(d.runs[0]):void 0}
                  onPointerEnter=${()=>Ce.set(d.runs[0]??null)}>
                <td>${d.label}${d===i?s` <${be} tip="the others are compared to this row">baseline<//>`:null}${d.queued?s` <${be}>queued<//>`:null}</td>
                ${d.scores.map((m,p)=>Po(m,d.live,i?.scores[p]??null))}
              </tr>`})}
          </tbody>
        </table></div>`:s`<div class="skeleton late" style="block-size: 120px"></div>`}
  <//>`}function Po(e,t,n){if(!e)return s`<td class="num muted">–</td>`;let o=n&&n!==e?`${e.mean-n.mean>=0?"+":"\u2212"}${Y(Math.abs(e.mean-n.mean))} against the baseline`:"",r=`${St(e.mean)}${e.std===null?"":` \xB1 ${St(e.std)}`}, ${e.n} run${e.n>1?"s":""}${o?`. ${o}`:""}`,a=`num score${e.best?" best":""}${t?" live":""}`;return s`<td class=${a} style=${e.shade===null?void 0:`--shade: ${e.shade}`} data-tip=${r}>
    ${Y(e.mean)}${e.std===null?null:s`<span class="spread"> ± ${Y(e.std)}</span>`}</td>`}var Ds={section:Es,row:Ts,grid:zt,line:Pn,table:On,scorecard:Ns,stat:In,images:Cs,text:Ss,proposal:ls,note:hs,output:$s,config:ws,memory:cs,groups:ds,notes:us,tabs:Ms,scatter:Rn,bar:Ln,histogram:_n,data_table:En,timeline:Tn,custom:xs,markdown:fs},Ro=new Set(["line","scatter","bar","histogram"]);function ce({node:e}){return Ro.has(e.block)?s`<${Lo} node=${e} />`:s`<${Tt} node=${e} blocks=${Ds} />`}function Lo({node:e}){let t=G(B);return se(t.path).removed.includes(e.id)?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ve(t.path,[e.id])}>1 hidden · show</button></div>`:s`<${Tt} node=${e} blocks=${Ds} />`}function Ps(e,t){let n=e.split(`
`),o=t.split(`
`),r=n.length,a=o.length,l=Array.from({length:r+1},()=>new Uint32Array(a+1));for(let g=r-1;g>=0;g--)for(let m=a-1;m>=0;m--)l[g][m]=n[g]===o[m]?l[g+1][m+1]+1:Math.max(l[g+1][m],l[g][m+1]);let i=[],c=0,d=0;for(;c<r&&d<a;)n[c]===o[d]?(i.push({kind:"same",text:n[c]}),c++,d++):l[c+1][d]>=l[c][d+1]?i.push({kind:"removed",text:n[c++]}):i.push({kind:"added",text:o[d++]});for(;c<r;)i.push({kind:"removed",text:n[c++]});for(;d<a;)i.push({kind:"added",text:o[d++]});return i}function Rs(e,t=3){let n=[],o=0;for(;o<e.length;){if(e[o].kind!=="same"){n.push(e[o++]);continue}let r=o;for(;r<e.length&&e[r].kind==="same";)r++;let a=o===0?0:t,l=r===e.length?0:t;r-o>a+l+1?n.push(...e.slice(o,o+a),{kind:"skip",count:r-o-a-l},...e.slice(r-l,r)):n.push(...e.slice(o,r)),o=r}return n}var Ht={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function Ls(e){if(Ht[e.block])return Ht[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(r=>Ht[r.block])),[o]=n;if(n.size===1&&o)return o}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function wt(e){let t=w(qe(e.path)),n=de(),o=R(t.data),r=ze(()=>tt(o.map(p=>p["run.id"]),n),[t.data,n]),a=ze(()=>new Map(o.map(p=>[p["run.id"],p["run.name"]??p["run.id"]])),[t.data]),l=se(e.path),i=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${i}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${O} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let c=e.view.view,d={path:e.path,colors:r,names:a,metrics:e.view.metrics??{},charted:At(c),pins:l.main??e.view.pins??[]};if(e.plain)return s`<div class=${i}><${B.Provider} value=${d}><${ce} node=${c} /><//></div>`;let g=c.block==="section"&&!c.props.title?c.children??[]:[c],m=g.map(p=>At(p).size>0).lastIndexOf(!0);return s`<div class=${i}>${e.before}
    <${B.Provider} value=${d}>
      ${g.map((p,$)=>{let v=Ls(p);return s`<${Ft} key=${p.id}><${O} label=${v}><${nt.Provider} value=${v}><${ce} node=${p} /><//><//>
          ${$===m?s`<${Bt} root=${c} />`:null}<//>`})}
      ${m===-1?s`<${Bt} root=${c} />`:null}
    <//>
  </div>`}function At(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])At(n,t);return t}function _s(e){if(null)return s`<div class="view-source small"><${k} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=M(F),o=n.page==="group"&&n.version,r=t.versions?s`<a href=${S(e.path,{history:!0})}><${k} name="history" size=${14} /> history (${t.versions})</a>`:null,a;switch(t.source){case"draft":a=s`draft <b>${t.draft}</b>`;break;case"view":a=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${j(ye(t.version))} by ${t.author??"unknown"}`;break;default:a=s`the built-in view`}return s`<div class="view-source small">
    <${k} name="layout" size=${14} /><span>${a}</span>
    ${o?s`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!o?s`<${_o} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||o?null:s`<${Io} path=${e.path} />
        <${Oo} path=${e.path} view=${t} />`}
  </div>`}function _o(e){let[t,n]=y(null),o=e.outdated.map(a=>a.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Fn(e.path)}catch(a){n(a.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${o} exists; update re-pins this view to it (a new version)`}>
      <${k} name="update" size=${14} /> update ${o}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Io(e){let[t,n]=y(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Le.set(await ct(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${k} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Oo(e){let t=se(e.path),n=un(t),[o,r]=y(!1),[a,l]=y(e.view.title??""),[i,c]=y(e.view.finding??""),[d,g]=y(null),[m,p]=y(!1);if(!n&&!o)return null;let $=async v=>{v.preventDefault(),p(!0),g(null);try{let E={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await U("save_view",{path:e.path,prefs:E,title:a,finding:i}),rt(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),Me(h=>["view","view_history","summary"].includes(h.method)&&h.scope===e.path),r(!1)}catch(E){g(E.message)}finally{p(!1)}};return o?s`<form class="save-form" onSubmit=${$}>
    <${Ue} label="Title"><input value=${a} onInput=${v=>l(v.target.value)} /><//>
    <${Ue} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${v=>c(v.target.value)} /><//>
    <div class="save-actions">
      <${ie} type="submit" icon=${m?"hourglass":"save"} disabled=${m}>${m?"Saving\u2026":"Save as view"}<//>
      <${ie} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${d?s`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:s`<${ie} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function Is(e){let t=w(Zn(e.path)),n=t.data?.entries??[],[o,r]=y(null),a=o??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let c=a.includes(i)?a.filter(d=>d!==i):[...a,i].slice(-2);r(c.sort())};return t.status==="error"?s`<${z} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${k} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,c)=>s`<li key=${i.version} class=${a.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${a.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${j(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${c===0?S(e.path):S(e.path,{version:i.version})}
            onClick=${d=>{d.preventDefault(),N(c===0?S(e.path):S(e.path,{version:i.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${a.length===2?s`<${zo} path=${e.path} a=${a[0]} b=${a[1]} />`:null}
  </section>`}function zo(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=w(t(e.a)).data,o=w(t(e.b)).data,r=w($e(e.path,e.a)).data,a=w($e(e.path,e.b)).data,l=n&&o?Rs(Ps(n.yaml,o.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${j(ye(e.a))} to ${j(ye(e.b))}</h3>
    <pre class="diff code">${l.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${wt} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${a?.title??e.b}</h3><${wt} path=${e.path} view=${a} plain /></div>
    </div>
  </div>`}function Os(e){return Qn(e.path),e.history?s`<div class="page"><div class="sections">
      <${O} label=${zs(e.path)}><${_t} path=${e.path} /><//>
      <${O} label="history"><${Is} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${Bo} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function Bo(e){let t=se(e.path).main,n=yt($e(e.path,e.version,e.draft,t),`${e.path}|${e.version}|${e.draft}`);T(()=>{n.status==="ready"&&requestAnimationFrame(Qt)},[n.status==="ready"]),T(()=>{let r=a=>vs(a.target.closest?.(".chart-frame")??null);return addEventListener("click",r,!0),()=>removeEventListener("click",r,!0)},[]);let o=s`
    <${O} label=${zs(e.path)}>
      <${_t} path=${e.path} finding=${n.data?.finding} />
      ${n.data?s`<${_s} path=${e.path} view=${n.data} />`:null}
    <//>
    ${re(e.path.split("/").pop()??"")?null:s`<${bs} path=${e.path} />`}`;return n.status==="error"?s`<div class="sections">${o}
      <${O} label="view">
        ${Ho(e.path,n.error)?s`<${z} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:s`<${z} kind="error">${n.error}<//>`}
      <//>
    </div>`:s`<${wt} path=${e.path} view=${n.data} before=${o} />`}function zs(e){return re(e.split("/").pop()??"")?"run":"group"}function Ho(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Bs(e){T(()=>{Te($e(e.id)).then(n=>N(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=w($e(e.id));return t.status==="error"?s`<div class="page"><${z} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var Ao={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Kt=20,Oe=-1,Ko=[["day",86400],["week",7*86400],["month",30*86400]];function As(e){let t=R(w(ue()).data).map(i=>i.path),n=w({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),o=w({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Ye("Timeline",R(n.data).filter(i=>i["run.status"]==="running").length);let r=Date.now()/1e3,a=R(n.data).filter(i=>i["run.created_at"]).map((i,c)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:c})),l=(o.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(ye(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${O} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Ue} label="Group" inline>
          <select value=${e.from} onChange=${i=>N(Ze(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${a.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${O} label="runs">
      ${n.status==="error"?s`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&o.data?s`<${Uo} bars=${a} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function Uo(e){let t=de(),n=L(null),o=[...e.bars.flatMap(h=>[h.start,h.end]),...e.marks.map(h=>h.t)],r=o.length?Hs(Math.min(...o),Math.max(...o)):Hs(Date.now()/1e3-86400,Date.now()/1e3),[a,l]=y(r),i=e.bars.length,c=Math.min(900,Math.max(160,(i+1.5)*Kt+40)),g=Nn(n,Dn,t?(h=>{let x=Cn(a[0],a[1]),u=b=>h.colors[Ao[b]??"muted"],f=b=>h.colors[b==="verdict"?"good":b==="decision"?"accent":b==="question"?"warn":"muted"];return{style:on(h),height:c,x:{range:a,log:!1,format:b=>Sn(b,x.step),label:"",splits:x.at},y:{range:[Oe-.8,i+.5],log:!1,reverse:!0,label:"",size:150,splits:i<=40?[Oe,...e.bars.map(b=>b.lane)]:[Oe],format:b=>b===Oe?"notes":Go(e.bars[Math.round(b)]?.name??"")},draw:({ctx:b,x:K,y:H,px:V,focused:A})=>{let Z=Kt*.62*V;for(let _ of e.bars){let P=K(_.start),C=Math.max(3*V,K(_.end)-P);b.fillStyle=A!==null&&A!==_.id?sn(u(_.status),.35):u(_.status),b.beginPath(),b.roundRect(P,H(_.lane)-Z/2,C,Z,3*V),b.fill()}for(let _ of e.marks){let P=K(_.t),C=H(Oe),ne=(A===_.id?6:4.5)*V;b.fillStyle=f(_.type),b.beginPath(),b.moveTo(P,C-ne),b.lineTo(P+ne,C),b.lineTo(P,C+ne),b.lineTo(P-ne,C),b.closePath(),b.fill()}},hit:(b,K,H,V)=>{if(Math.abs(K-V(Oe))<Kt/2){let _=Vo(e.marks,P=>Math.abs(H(P.t)-b),8);return _?{key:_.id,rows:Wo(_)}:null}let A=Math.round((K-V(0))/(V(1)-V(0))),Z=e.bars.find(_=>_.lane===A&&H(_.start)-3<=b&&b<=Math.max(H(_.end),H(_.start)+3)+3);return Z?{key:Z.id,rows:Fo(Z)}:null},onClick:b=>{let K=e.marks.find(H=>H.id===b);K?N(S(K.group,{drawer:!0})):N(ae(b))}}})(t):null,[a,e.bars,e.marks],t),m=h=>{if(!g.current)return;h.preventDefault();let x=g.current.xAt(h.clientX),u=Math.exp(h.deltaY*.0015);l(([f,b])=>Ut([x-(x-f)*u,x+(b-x)*u],r))},p=L(null),$=h=>p.current={x:h.clientX,range:a},v=h=>{if(!p.current||!g.current||!(h.buttons&1))return;let x=(h.clientX-p.current.x)*g.current.xPerPixel(),[u,f]=p.current.range;Math.abs(h.clientX-p.current.x)>3&&l(Ut([u-x,f-x],r))},E=Math.max(...o,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Ko.map(([h,x])=>s`<button type="button" role="radio" aria-checked=${Math.abs(a[1]-a[0]-x)<1}
          onClick=${()=>l(Ut([E-x,E+x*.02],[Math.min(r[0],E-x),r[1]]))}>last ${h}</button>`)}
      <button type="button" role="radio" aria-checked=${a[0]===r[0]&&a[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${m} onPointerDown=${$} onPointerMove=${v} onPointerUp=${()=>p.current=null}></div>
    <p class="muted small">${jo(t)}</p>
  </div>`}function Fo(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:j(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Ee(e.end-e.start),color:null}]}function Wo(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:j(new Date(e.t*1e3).toISOString()),color:null}]}function jo(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Vo(e,t,n){let o=null,r=n;for(let a of e){let l=t(a);l<r&&([o,r]=[a,l])}return o}function Hs(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Ut([e,t],n){let o=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-o));return[r,r+o]}function Go(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function Ks(){let e=M(De),t=L(null);if(T(()=>{let r=t.current;if(!r||!e)return;r.showModal();let a=()=>De.set(null);return r.addEventListener("close",a),()=>r.removeEventListener("close",a)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},o=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${o} closedby="any">
    <${B.Provider} value=${e.view}><${ce} node=${n} /><//>
  </dialog>`}function Us(e,t){let n=e.toLowerCase(),o=t.toLowerCase();if(!n)return 1;let r=o.indexOf(n);if(r>=0)return 100-Math.min(r,50)-o.length/100;let a=0,l=0;for(let i of o)if(i===n[a]?a++:a>0&&l++,a===n.length)return 40-Math.min(l,39);return 0}function Ws(e){let[t,n]=y(e.query),[o,r]=y(0),a=L(null),l=R(w(ue()).data),i=R(w(ut()).data);T(()=>{let u=a.current;u.showModal();let f=()=>te.set(null);u.addEventListener("close",f);let b=!1,K=A=>{let Z=u.getBoundingClientRect();return A.clientX<Z.left||A.clientX>Z.right||A.clientY<Z.top||A.clientY>Z.bottom},H=A=>b=K(A),V=A=>b&&K(A)&&u.close();return"closedBy"in HTMLDialogElement.prototype||(u.addEventListener("pointerdown",H),u.addEventListener("pointerup",V)),()=>{u.removeEventListener("close",f),u.removeEventListener("pointerdown",H),u.removeEventListener("pointerup",V)}},[]);let c=()=>a.current?.close(),d=u=>()=>N(u),g=F.value,m=g.page==="group"?g.path:".",p=(u,f,b,K)=>({section:"Commands",label:u,detail:f,sym:{icon:b,tone:"muted",label:u},run:K}),v=[...l.map(u=>({section:"Groups",label:u.path==="."?"local":u.path,detail:`${u.runs} runs${u.proposal?` \xB7 ${u.proposal}`:""}`,sym:D("research",u.status),run:d(S(u.path))})),...i.map(u=>({section:"Runs",label:u["run.name"]??u["run.id"],detail:`${u["run.status"]} \xB7 ${u["run.path"]}`,sym:D("run",u["run.status"]),run:d(S(u["run.path"]))})),p("Theme: light","","sun",()=>et("light")),p("Theme: dark","","moon",()=>et("dark")),p("Theme: follow the system","","monitor",()=>et("system")),p("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),p("Show notes and timeline","i","file-text",d(S(m,{drawer:!0}))),p("Show or hide the sidebar","\u2318B","panel-left",()=>ee.set(!ee.value)),p(oe.value?"Resume live updates":"Pause live updates","p",oe.value?"play":"pause",()=>oe.set(!oe.value)),p("Keyboard shortcuts","?","keyboard",()=>fe.set(!0)),p("Settings","","settings",d("/settings/appearance"))].map(u=>({it:u,s:Math.max(Us(t,u.label),Us(t,u.detail)*.5)})).filter(u=>u.s>0).sort((u,f)=>f.s-u.s||Fs(u.it.section)-Fs(f.it.section)).slice(0,60).map(u=>u.it),E=u=>{u&&(c(),u.run())},h=u=>{if(u.key==="ArrowDown")r(Math.min(v.length-1,o+1));else if(u.key==="ArrowUp")r(Math.max(0,o-1));else if(u.key==="Enter")E(v[o]);else return;u.preventDefault()},x="";return s`<dialog class="sheet" ref=${a} aria-label="Search" closedby="any">
    <div class="palette-input"><${k} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${v[o]?`pal-${o}`:void 0}
        onInput=${u=>{n(u.target.value),r(0)}} onKeyDown=${h} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${v.map((u,f)=>{let b=u.section!==x&&!t?x=u.section:null;return s`${b?s`<li class="palette-head small" role="presentation">${b}</li>`:null}
          <li id=${`pal-${f}`} class="item" role="option" aria-selected=${f===o}
              onMouseMove=${()=>r(f)} onClick=${()=>E(u)}>
            <${I} spec=${u.sym} /><span class="label">${u.label}</span><span class="detail small">${u.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function Fs(e){return["Groups","Runs","Commands"].indexOf(e)}function kt(e,t=[]){let n=new Map,o=(i,c={})=>({path:i,name:i==="."?"local":i.split("/").pop(),runs:c.runs??0,running:c.running??0,failed:(c.failed??0)+(c.killed??0)+(c.lost??0),status:c.status??null,children:[]});for(let i of e)n.set(i.path,o(i.path,i));(t.length===0||t.some(i=>i.name==="local"))&&!n.has(".")&&n.set(".",o("."));for(let i of t){let c=i.name==="local"?".":i.name;n.has(c)||n.set(c,o(c)),Object.assign(n.get(c),{state:i.state,error:i.error})}for(let i of n.values()){if(q(i.path))continue;let c=i.path.lastIndexOf("/"),d=c<0?".":i.path.slice(0,c);(n.get(d)??n.get(xe(i.path))??n.get(".")).children.push(i)}for(let i of n.values())i.children.sort((c,d)=>c.name.localeCompare(d.name));let a=[...n.values()].filter(i=>i.path!=="."&&q(i.path)).sort((i,c)=>i.name.localeCompare(c.name)),l=n.get(".");return l?[l,...a]:a}function js(e,t,n,o=new Set){let r=[],a=n.toLowerCase(),l=i=>{(!a||i.path.toLowerCase().includes(a)||Vs(i,a))&&(r.push(i),(a||(q(i.path)?!o.has(i.path):t.has(i.path)))&&i.children.forEach(l))};return e.forEach(l),r}function Vs(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Vs(n,t))}function Gs(e,t){if(q(t))return e;let n=t.lastIndexOf("/"),o=n<0?".":t.slice(0,n),r=a=>a.path===o?a:a.children.map(r).find(l=>l)??null;return e.map(r).find(a=>a)?.children??[]}function qs(e){return q(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Xs(){let e=M(F),t=w(ue()),[n,o]=y(()=>new Set(ge("open",[]))),[r,a]=y(()=>new Set(ge("closed-hosts",[]))),[l,i]=y(""),c=L(null),d=e.page==="group"?e.path:null,g=kt(R(t.data),t.data?.meta?.sources??[]),m=js(g,Yo(n,d),l,r),p=h=>q(h)?!r.has(h):n.has(h),$=(h,x)=>{let u=x??!p(h);if(q(h)){let b=new Set(r);u?b.delete(h):b.add(h),ve("closed-hosts",[...b]),a(b);return}let f=new Set(n);u?f.add(h):f.delete(h),ve("open",[...f]),o(f)},v=L(d);return T(()=>{d!==v.current&&d&&!q(d)&&r.has(xe(d))&&$(xe(d),!0),v.current=d},[d]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${k} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${l} aria-label="Filter groups"
        onInput=${h=>i(h.target.value)} />
    </label>
    <div class="tree" ref=${c} onKeyDown=${h=>{let x=[...c.current?.querySelectorAll("a.tree-item")??[]],u=x.indexOf(document.activeElement),f=m[u];switch(h.key){case"ArrowDown":x[Math.min(x.length-1,u+1)]?.focus();break;case"ArrowUp":x[Math.max(0,u-1)]?.focus();break;case"ArrowRight":f?.children.length&&$(f.path,!0);break;case"ArrowLeft":f?.children.length&&p(f.path)?$(f.path,!1):f&&x[m.findIndex(b=>b.path===Xo(f.path))]?.focus();break;default:return}h.preventDefault()}} role="tree">
      ${m.map(h=>s`<${qo} key=${h.path} node=${h} current=${h.path===d}
        open=${p(h.path)||!!l} onToggle=${()=>$(h.path)} />`)}
    </div>
  </nav>`}function qo(e){let t=e.node,n=()=>Xe(t.path),o=t.children.length>0,r=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${q(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${o?e.open:void 0}
      style=${`padding-inline-start:${8+qs(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${a=>{a.metaKey||a.ctrlKey||(a.preventDefault(),N(S(t.path)))}}>
    <span class="twisty" onClick=${a=>{a.preventDefault(),a.stopPropagation(),e.onToggle()}}>
      ${o?s`<${k} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${q(t.path)?s`<${I} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${I} spec=${D("run","running")} size=${14} />`:null}
      ${t.failed?s`<${I} spec=${{...D("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Xo(e){if(q(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function Yo(e,t){if(!t||t===".")return e;let n=new Set(e),o=t.split("/");for(let r=1;r<o.length;r++)n.add(o.slice(0,r).join("/"));return n}function Js(){let e=M(F),t=M(ee),n=M(te),o=M(fe),r=L(null);T(()=>Zt(()=>r.current),[]),T(()=>(addEventListener("keydown",Ys),()=>removeEventListener("keydown",Ys)),[]);let a=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${Os} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=s`<${Bs} id=${e.id} />`;break;case"settings":l=s`<${ss} />`;break;case"timeline":l=s`<${As} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return me||!1?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${a?" with-drawer":""}`}>
    <${rs} />
    ${t?s`<${Xs} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${a?s`<${gs} path=${e.path} run=${e.run} />`:null}
    <${as} />
    ${n!==null?s`<${Ws} query=${n} />`:null}
    ${o?s`<${Zo} />`:null}
    <${Ks} />
  </div>`}function Ys(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),te.set(te.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),ee.set(!ee.value);return}if(e.key==="Escape"){if(te.value!==null||fe.value)return;let o=F.value;return o.page==="group"&&o.run?N(S(o.path,{drawer:!0}),{replace:!0}):o.page==="group"&&o.drawer?N(S(o.path),{replace:!0}):void 0}if(t||e.altKey||ts(e)||te.value!==null||fe.value)return;let n=F.value;switch(e.key){case"/":e.preventDefault(),te.set("");break;case"?":fe.set(!fe.value);break;case"p":oe.set(!oe.value);break;case"i":n.page==="group"&&N(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":ee.set(!ee.value);break;case"[":case"]":n.page==="group"&&Jo(n.path,e.key==="]"?1:-1);break}}async function Jo(e,t){let n=await Te(ue()),o=Gs(kt(R(n),n?.meta?.sources??[]),e),r=o.findIndex(l=>l.path===e),a=o[r+t];a&&N(S(a.path))}function Zo(){let e=L(null);return T(()=>{let t=e.current;t.showModal();let n=()=>fe.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${$t.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ie} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}en();if(me){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(pe.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Be.n,tn&&cn()}zn();var Qo=U("meta").then(e=>(me&&(e={...e,settings:{...e.settings,theme_mode:pe.value}}),ft(e),e));!me&&!!1&&Jt(async()=>{let[e,t]=await Promise.all([Qo,U("meta")]);e.bundle!==t.bundle?location.reload():ft(t)});Wt(s`<${Js} />`,document.getElementById("app"));
