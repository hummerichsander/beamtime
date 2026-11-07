import{$ as W,A as Wt,Aa as $n,B as ue,Ba as fn,C as Ie,Ca as hn,D as qt,E as qe,Ea as gn,F as $t,Fa as vn,G as me,Ga as bn,H as Zt,Ha as yn,I as ft,Ia as wn,J as Xe,Ja as kn,K as U,Ka as xn,L as Z,La as Sn,M as ie,N as Ye,O as Qt,P as Oe,Q as ze,S as en,T as tn,U as w,V as L,W as Je,X as se,Y as z,Z as P,_ as Be,a as s,aa as nn,ba as I,ca as ae,d as K,da as Ae,e as Le,ea as ht,f as Ce,fa as Ze,g as pt,ga as Qe,h as k,ha as E,i as Kt,ia as vt,j as te,ja as He,k as Ut,ka as et,l as Ft,la as bt,m as jt,ma as Se,n as Ee,na as tt,o as ne,oa as sn,p as C,pa as Ke,q as Ve,qa as an,r as de,ra as on,s as Re,sa as rn,t as we,ta as yt,u as V,ua as ln,v as q,w as Gt,xa as cn,y as _,ya as dn,z as Vt,za as un}from"./chunks/chunk-5D3YEJQT.js";import{a as At,b as Ht}from"./chunks/chunk-O2K4N3UR.js";import{A as Yt,B as Jt,C as j,F as ve,G as ke,H as xe,I as F,J as gt,U as mn,V as pn,c as zt,e as y,f as T,g as Bt,h as O,i as _e,j as J,m as ye,n as N,o as he,p as ge,u as Xt,w as We}from"./chunks/chunk-24GOVU2B.js";import"./chunks/chunk-VC46IEJQ.js";function Te(e,t){Ee(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var wt=["notes","timeline","groups","check","card","memory_show","status"];async function nt(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Te(e.group,wt)}async function Cn(e,t,n,a){await K("note_add",{group:e,type:t,description:n,body:a}),Te(e,wt)}async function En(e,t){await K("memory_update",{group:e,body:t}),Te(e,["memory_show","status"])}async function Tn(e,t){let n=await K("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([o])=>!["schema","author","user","supersedes"].includes(o)));await K("proposal_set",{group:e,proposal:{...a,statement:t}}),Te(e,["groups","proposal_show","check","summary"])}async function Mn(e){await K("note_rm",{note:e.id}),Te(e.group,wt)}async function Nn(e,t,n){await K("name",{run:e,name:n}),Te(t,["card","runs","groups","summary","series"])}async function st(e,t,n){let a=await K("view_text",{path:e,id:t,text:n});return Ee(o=>["view","view_history"].includes(o.method)&&o.scope===e),a.id}async function Dn(e){await K("view_upgrade",{group:e}),Ee(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Me=new ye(null);async function Pn(e,t){return await K("set",{key:e,value:t}),K("meta")}var le=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),pe=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),kt=e=>({method:"summary",params:{path:e},scope:e}),Ne=e=>({method:"groups",params:{from:e,depth:0},scope:e}),_n=e=>({method:"check",params:{group:e},scope:e}),Ln=e=>({method:"proposal_show",params:{group:e},scope:e}),De=(e,t)=>({method:"card",params:{run:Re(e,t)},scope:t}),Rn=(e,t)=>({method:"output",params:{run:Re(e,t),tail:30},scope:t}),Ue=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),at=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),In=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),On=()=>({method:"status",params:{},scope:"."}),ot=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Fe(e){for(let t of[pe(e),Ne(e),Ue(e),kt(e)])pt(t);Ce(pe(e)).then(t=>{for(let n of zn(t.view))pt(n)}).catch(()=>{})}function zn(e){return e?[...Os.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(zn)]:[]}var Os=new Set(["line","custom"]),Bn=e=>({method:"view_history",params:{group:e},scope:e});var xt="/static/favicon.svg",rt=null;async function zs(){if(rt)return rt;let e=new Image;e.src=xt,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let a=n.getContext("2d");if(!a)return xt;a.drawImage(e,0,0,t,t),a.beginPath(),a.arc(t-6,t-6,6,0,Math.PI*2);let o=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return a.fillStyle=o||"#2f5aa8",a.fill(),rt=n.toDataURL("image/png"),rt}function Bs(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=xt;return}zs().then(n=>{t.type="image/png",t.href=n})}}function je(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,Bs(t>0)},[e,t])}function An(e){let t=ne(e.split("/").pop()??""),n=k(t?null:Ne(e)),a=k(t?De(e.split("/").pop()??"",e):null),o=t?a.data?.run.name??a.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,i=t?a.data?.run.status==="running"?1:0:P(n.data)[0]?.running??0;je(o,i)}var Q=new ye(he("sidebar",!0)),ee=new ye(null),$e=new ye(!1),fe=new ye(null);Q.subscribe(e=>ge("sidebar",e));var Hn=he("visit",Date.now());ge("visit",Date.now());function Kn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var it=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var As=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function lt(e){fe.set(e),qe.set(e.theme),We.set(e.colormaps),e.settings?.theme_mode&&me.set(e.settings.theme_mode),ft()}var Un=0;async function St(e,t){let n=++Un;e==="theme_mode"&&(me.set(t),ft());let a=await Pn(e,t);n===Un&&lt(a)}function Fn(){let e=N(me),t=ie(),n=N(fe),[a,o]=y(null);je("Settings");let i=(l,u)=>{o(null),St(l,u).catch(f=>o(f.message))},c=n?.settings??{},r=(l,u,f)=>s`
    <label class="field-label small" for=${`setting-${l}`}>${u}</label>
    <span class="input body">
      <select id=${`setting-${l}`} value=${c[l]} onChange=${d=>i(l,d.target.value)}>
        ${f.map(d=>s`<option value=${d}>${d}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${I} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${c.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${a?s`<${z} kind="error">${a}<//>`:null}
    <//>
    <${I} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${As.map(([l,u,f])=>s`<button type="button" role="radio" aria-checked=${e===l} onClick=${()=>i("theme_mode",l)}>
            <${w} name=${u} size=${15} />${f}</button>`)}
        </div>
        ${r("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(l=>s`<${z} kind="warning">${l}<//>`)}
    <//>
    <${I} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${Qe} options=${n.figure_styles} value=${c.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${l=>i("figure_style",l)} />`:s`<span class="muted small"><code>${JSON.stringify(c.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(c.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${I} label="keyboard">
      <table class="kv">${it.map(([l,u])=>s`<tr><td><kbd class="small">${l}</kbd></td><td>${u}</td></tr>`)}</table>
    <//>
    <${I} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(l=>s`
          <tr><td class="muted">${l.name}</td><td><code class="code">${l.logdir}</code> (${l.kind}, ${l.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var jn={system:"light",light:"dark",dark:"system"},Hs={system:"monitor",light:"sun",dark:"moon"};function Gn(){let e=N(fe),t=N(me),n=N(Q);return s`<header class="topbar">
    <${W} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Q.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>ee.set("")} aria-label="Search (⌘K)">
      <${w} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Ks} />
      <${W} icon=${Hs[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${jn[t]})`}
        onClick=${()=>{St("theme_mode",jn[t])}} />
      <a class="icon-button" href=${Ve(q.value.page==="group"?q.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${w} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${w} name="settings" size=${16} /></a>
    </div>
  </header>`}function Ks(){let t=(k(le()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${C(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${w} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${w} name="server" size=${15} /> local</span>`}function Us(e){let[t,n]=y(Date.now());return T(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function Fs(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function Vn(){let e=N(Ut),t=N(te),n=N(Ft),a=N(q),o=Us(5e3),i=k(On()).data,c=P(k(ot()).data),r=N(fe),l=i?.daemon,u=i?.runs?.running??0,f=c.filter(M=>M["run.status"]==="failed"&&Fs(M["run.ended_at"])>Hn).length,d=i?.meta?.freshness,[h,$,g]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&l?["",`live \xB7 updated ${F(new Date(n).toISOString(),o)}`,`beamtime serve, pid ${l.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${g}><span class=${`live-dot ${h}`}></span>${$}</span>
    ${u?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>ee.set("running")}>
          <${w} name="circle-dot" size=${14} class="tone-accent" />${u} running</button>`:null}
    ${f?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>ee.set("failed")}>
          <${w} name="circle-x" size=${14} />${f} failed since your last visit</button>`:null}
    ${d?.behind?s`<span class="status-item warn-text" data-tip=${d.text}><${w} name="hourglass" size=${14} />${d.behind} runs behind</span>`:null}
    ${d?.damaged?.length?s`<span class="status-item warn-text" data-tip=${d.damaged.join(`
`)}><${w} name="triangle-alert" size=${14} />${d.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${w} name="activity" size=${14} />1 run selected</span>`:null}
    <${W} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>te.set(!t)} />
    ${r?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${r?.version?`beamtime ${r.version}`:""}</span>
  </footer>`}var Wn=null;function ct(e){let t=O(null),[n,a]=y(null),[o,i]=y(!1),[c,r]=y(!1);T(()=>{let d=!0;return Wn??=import("./chunks/md-SW3VT2BQ.js"),Wn.then(h=>h.render(e.text??"")).then(h=>d&&a(h)),()=>{d=!1}},[e.text]),Bt(()=>{let d=t.current;if(!d||!e.clamp)return;let h=()=>r(d.scrollHeight>d.clientHeight+2),$=new ResizeObserver(h);return $.observe(d),()=>$.disconnect()},[e.clamp,n]);let l=e.clamp&&!o,u=`md${l?" clamped":""}`,f=l?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${u} ref=${t} style=${f}>
          ${(e.text??"").split(/\n{2,}/).map(d=>s`<p>${d}</p>`)}
        </div>`:s`<div class=${u} ref=${t} style=${f} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(c||o)?s`<button type="button" class="link small more" onClick=${()=>i(!o)}>${o?"less":"more"}</button>`:null}
  </div>`}function be(e){let[t,n]=y(!!e.startEditing),[a,o]=y(e.value),[i,c]=y(null),[r,l]=y(null),u=O(null),f=O(!1);T(()=>c(null),[e.value]),T(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[d,h]=y(!1),$=e.locked??void 0,g=p=>{if(!p.target.closest("a, button, input, summary")){if($)return h(!0);p.preventDefault(),o(i??e.value),l(null),f.current=!1,n(!0)}},M=()=>{f.current=!0,n(!1),l(null),e.onCancel?.()},v=async()=>{if(f.current)return;f.current=!0;let p=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if(p===e.value.trim()||!p&&!e.multiline)return M();n(!1),c(p);try{await e.onSave(p)}catch(b){c(null),o(p),l(b.message),f.current=!1,n(!0)}},x=p=>{if(p.key==="Escape")return p.preventDefault(),p.stopPropagation(),M();p.key!=="Enter"||p.isComposing||p.keyCode===229||(!e.multiline||p.metaKey||p.ctrlKey)&&(p.preventDefault(),v())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${p=>o(p.target.value)} onKeyDown=${x} onBlur=${v}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${r?s` · <span class="bad-text">${r}</span>`:null}</span>
    </div>`;let m=i??e.value;return s`<div class=${`editable${$?" locked":""}${i!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${$?`${e.label}: ${$}`:`Edit ${e.label}`}
      data-tip=${$} onClick=${g} onBlur=${()=>h(!1)}
      onKeyDown=${p=>p.key==="Enter"&&p.target===p.currentTarget&&g(p)}>
    ${m.trim()?e.render?e.render(m):m:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${d&&$?s`<span class="edit-hint small locked-why" role="status"><${w} name="lock" size=${14} /> ${$}</span>`:null}
  </div>`}function Ct(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${j(e.ci[0])}, ${j(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${j(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${j(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function Et(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function qn({node:e}){let t=Z("proposal"),n=Z("check"),a=t.data,o=n.data;if(!a)return s`<${se} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let i=a.proposal??{},c=(a.versions??[]).filter(l=>l.version!==a.version),r=!e.props.of||e.props.of===".";return s`<${se} title="Predictions" result=${t} class="proposal">
    ${r?null:s`<p class="statement">${i.statement}</p>`}
    ${i.rationale?s`<p class="rationale prose">${i.rationale}</p>`:null}
    <div class="predictions">
      ${(o?.predictions??[]).map(l=>s`<div class="prediction" key=${l.name}>
          <${L} spec=${E("result",l.result)} />
          <span class="pname">${l.name}</span>
          <span class="pdetail num small">${Ct(l)}</span>
        </div>`)}
    </div>
    ${c.length?s`<${ht} summary=${`${c.length} earlier version${c.length>1?"s":""}`}>
          ${c.map(l=>s`<p class="small"><code>${l.version}</code> ${l.statement}
            <span class="muted">(${l.runs} runs, check ${l.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function Xn({node:e}){let t=Z("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],o=a.find(r=>r.group===n)??null,i=a.filter(r=>r.group!==n),c=o?.notes_since?"out of date":o?`version ${o.versions??1}`:"none yet";return s`<${Be} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?c:void 0} open=${!1} result=${t}
      action=${s`<${L} spec=${{icon:"circle-help",tone:"muted",label:Gs}} />`}>
    <${be} value=${o?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${r=>s`<${ct} text=${r} />`} onSave=${r=>En(n,r)} />
    ${o&&(o.body?.length>(t.data?.budget??1/0)||o.notes_since>=js)?s`<p class="memory-meta small warn-text">${o.body?.length>t.data.budget?`${o.body.length} characters, beyond the budget of ${t.data.budget}`:`${o.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${o?s`<p class="memory-meta small">${o.author} · covers notes until ${o.covers_until?.slice(0,10)}
          ${o.notes_since?s` · <span class="warn-text">${o.notes_since} newer note${o.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${i.length?s`<p class="memory-meta small">Memory above this group: ${i.map((r,l)=>s`${l?", ":""}<a href=${C(r.group)}>${r.group==="."?"local":r.group}</a>`)}</p>`:null}
  <//>`}var js=5,Gs="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Vs="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function Yn({node:e}){let t=Z("main"),n=e.data?.main.params.from??".",a=P(t.data).filter(o=>o.path!==n);return s`<${se} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(o=>{let[i,c]=Et(o.progress),r=(o.failed??0)+(o.killed??0)+(o.lost??0);return s`<a class="group-row" key=${o.path} href=${C(o.path)}
            onPointerEnter=${()=>Fe(o.path)} onFocus=${()=>Fe(o.path)}>
          <${L} spec=${E("research",o.status)} />
          <span class="gname heading">${o.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${o.status!=="concluded"?s`<span class=${`tone-${E("research",o.status).tone}`}>${E("research",o.status).label}</span>`:null}
            ${o.check?s`<${L} spec=${E("result",o.check)} word />`:null}
            ${o.verdict?s`<${L} spec=${E("verdict",o.verdict)} />`:null}
            ${i?s`<span data-tip=${c}>${i}</span>`:null}
            <span class="num"><b>${o.runs}</b> runs</span>
            ${o.running?s`<${L} spec=${E("run","running")} />`:null}
            ${r?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${w} name="circle-x" size=${14} /> ${r}</span>`:null}
          </span>
          ${o.proposal?s`<span class="gstatement caption">${o.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Jn({node:e}){let t=Z("main"),n=e.data?.main.params.from??".",[a,o]=y(!1),i=(t.data?.entries??[]).filter(r=>!String(r.state??"").startsWith("superseded")),c=t.data?.meta?.matched??i.length;return s`<${Be} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(c):void 0} result=${t}
      action=${s`<${L} spec=${{icon:"circle-help",tone:"muted",label:Vs}} />
        ${s`<${W} icon="plus" label="Add a note" onClick=${()=>o(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${Xs} group=${n} onDone=${()=>o(!1)} />`:null}
      ${t.data&&!i.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${i.map(r=>s`<${dt} key=${r.id} note=${r} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Zn} call=${e.data.main} before=${i[i.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Ws=20;function Zn(e){let[t,n]=y(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Ws}}:null,o=k(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(o.status==="error")return s`<p class="bad-text small">${o.error}</p>`;let i=o.data?.entries??[];return s`${o.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${i.map(c=>s`<${dt} key=${c.id} note=${c} scope=${e.scope} />`)}
    ${o.data?.more?s`<${Zn} call=${e.call} before=${i[i.length-1]?.id} scope=${e.scope} />`:null}`}var qs=["observation","decision","idea","question","theory"];function Qn(e){return(e?.note_types??qs).filter(t=>t!=="verdict")}function Xs(e){let t=Qn(N(fe)),[n,a]=y("observation"),[o,i]=y(""),[c,r]=y(""),[l,u]=y(null),[f,d]=y(!1),h=async g=>{if(g.preventDefault(),!o.trim())return u("give the note a title");d(!0);try{await Cn(e.group,n,o.trim(),c.trim()),e.onDone()}catch(M){u(M.message),d(!1)}};return s`<form class="note new-note" onSubmit=${h} onKeyDown=${g=>{g.key==="Escape"&&e.onDone(),g.key==="Enter"&&(g.metaKey||g.ctrlKey)&&h(g)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${g=>a(g.target.value)}>
        ${t.map(g=>s`<option value=${g}>${g}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${o} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${g=>i(g.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${c} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${g=>r(g.target.value)}></textarea></span>
    <div class="save-actions">
      <${ae} type="submit" icon=${f?"hourglass":"plus"} disabled=${f}>${f?"Adding\u2026":"Add note"}<//>
      <${ae} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${l?s`<span class="bad-text small">${l}</span>`:null}
    </div>
  </form>`}function Ys({note:e}){let t=Qn(N(fe)).filter(n=>n!==e.type);return e.type==="verdict"?s`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${w} name=${E("note","verdict").icon} size=${15} /></span>`:s`<${Ze} icon=${E("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>s`<button type="button" key=${n} onClick=${()=>nt(e,{type:n})}>
        <${w} name=${E("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function dt(e){let t=e.note,[n,a]=y(!!e.open),[o,i]=y(!1),c=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,r=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),l=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete, .popover-wrap")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${w} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${Ys} note=${t} />
      <${be} value=${t.description} label="the note's title" class="note-title heading" render=${Zs}
        onSave=${u=>nt(t,{description:u})} />
      ${t.overall?s`<${L} spec=${E("verdict",t.overall)} />`:null}
      ${t.state?s`<${nn} tone="warn">${t.state}<//>`:null}
      ${c?s`<a class="note-group small" href=${C(c)} data-tip="from this group">${Js(c,e.scope)}</a>`:null}
      <span class="note-meta small">${l?`${l} \xB7 `:""}${F(r)}</span>
      ${s`<${W} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${o}
        onClick=${u=>{u.stopPropagation(),i(!o)}} />`}
    </div>
    ${o?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ae} icon="trash" kind="danger" onClick=${()=>{Mn(t)}}>Delete<//>
          <${ae} icon="x" kind="quiet" onClick=${()=>i(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${be} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${u=>s`<${ct} text=${u} />`}
          onSave=${u=>nt(t,{body:u})} />`:null}
  </article>`}function Js(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return ne(a)?a.slice(-8):n}function es({node:e}){let t=Z("main"),n=t.data?.lines??[],a=t.data?.meta??{},o=s`<${w} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${se} result=${t}>
    <${ht} summary=${o} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function ts({node:e}){let t=J(U);return s`<${se} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${be} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Me.value===e.id} onCancel=${()=>Me.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${ct} text=${n} />`}
      onSave=${n=>(Me.set(null),st(t.path,e.id,n))} />
  <//>`}function ns({node:e}){return s`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Zs(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[o]=a.split(/[#@]/),i=o.split("/").pop()??"";return s`<a href=${ne(i)?de(i):C(o)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function ss(e){let t=()=>_(C(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${w} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${W} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${Qs} id=${e.run} scope=${e.path} />`:s`<${ea} path=${e.path} />`}
  </aside>`}function Qs({id:e,scope:t}){let n=k(De(e,t)).data,a=k(Rn(e,t)).data,o=k(Ue(t)).data,i=k({method:"keys",params:{from:t},scope:t}).data,c=ie(),r=_e(()=>Ye(P(o).map(d=>d["run.id"]),c).get(e),[o,c,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let l=n.run,u=Object.entries(n.metrics??{}),f=Xt(r,c);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${f.class} style=${f.style}></span>
      <a href=${de(e)}>${l.name}</a></h3>
    <p class="facts small">
      <${L} spec=${E("run",l.status)} word />
      <span><b>${ke(l.steps)}</b> steps</span>
      <span><b>${xe(l.duration_s)}</b></span>
      <span data-tip=${l.created_at}>${F(l.created_at)}</span>
    </p>
    ${l.error?s`<pre class="log code bad-text">${l.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <${et} config=${n.config??{}} varying=${He(i)} />
    ${u.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${u.map(([d,h])=>s`<tr><td>${d}</td><td class="num"><b>${j(h.last)}</b></td>
              <td class="num">${j(h.min)}</td><td class="num">${j(h.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(d=>s`<p class="small"><${L} spec=${E("note",d.type)} /> ${d.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(d=>s`<div class="event small"><span class="muted num">${d.t?.slice(5,16).replace("T"," ")}</span>
        <${w} name=${vt(d.type)} size=${14} /><span>${d.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function ea({path:e}){let t=k(at(e)).data,n=k(In(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${dt} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${w} name=${a.kind==="note"?"file-text":vt(a.type)} size=${14} />
        <span>${a.run?s`<a href=${de(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var Tt=["failed","killed","lost"];function Mt(e){let t=we(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=V(e.path)?[]:n.split("/"),o=a.length&&ne(a[a.length-1])?a[a.length-1]:null,i=a.slice(0,-1),c=r=>[...t==="."?[]:[t],...i.slice(0,r+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${C(t)}>${t==="."?"local":t}</a>`:null}
      ${i.map((r,l)=>s`<span>/</span><a href=${C(c(l))}>${r}</a>`)}
    </nav>
    ${o?s`<${sa} id=${o} scope=${e.path} />`:s`<${ta} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function ta({path:e}){let t=P(k(Ne(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=Tt.reduce((o,i)=>o+(t[i]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${L} spec=${E("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${Tt.filter(o=>t[o]).map(o=>`${t[o]} ${o}`).join(", ")}>
            <${w} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?Tt.find(o=>t[o]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${os} path=${e} />
    </p>`}function as({path:e}){let t=P(k(Ne(e)).data)[0]??null,n=k(t?.proposal?_n(e):null).data,a=k(t?.proposal?Ln(e):null).data;if(!t?.proposal)return null;let o=a?.proposal?.rationale,i=a?.versions?.find(l=>l.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[c,r]=Et(n?.progress?.text??t.progress);return s`<${I} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${be} value=${t.proposal} label="the proposal's statement" locked=${a?i:"Loading the proposal\u2026"}
          render=${l=>s`<span data-tip=${i?void 0:o}>${l}</span>`}
          onSave=${l=>Tn(e,l)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(l=>{let u=E("result",l.result),f=Ct(l),d=f?`${u.label}: ${f}`:u.label;return s`<span class=${`check small tone-${u.tone}`} key=${l.name} data-tip=${d}
              aria-label=${`${l.name}: ${d}`} tabindex="0"><${w} name=${u.icon} size=${14} />${l.name}</span>`})}
        ${n?.provisional||c?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${c?s`<span class="muted" data-tip=${r}>${n?.provisional?" \xB7 ":""}${c}</span>`:null}
            </span>`:null}
      </div>
      <${na} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function na(e){let t=k(e.verdict?at(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=E("verdict",e.verdict),a=(t?.entries??[]).find(i=>i.type==="verdict"&&(i.group??e.path)===e.path),o=a?ve(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${w} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${o}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${o?` \xB7 ${F(o)}`:""}</span>`:null}
  </p>`}function sa({id:e,scope:t}){let n=k(De(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,o=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${be} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${i=>Nn(a.id,t,i.trim())} />
      <${L} spec=${E("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${ke(a.steps)}</b> steps</span>
      <span><b>${xe(a.duration_s)}</b></span>
      ${n.progress?s`<${aa} run=${a} progress=${n.progress} />`:null}
      <span data-tip=${a.created_at}>${F(a.created_at)}</span>
      <${os} path=${t} />
      <${W} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${o} />
      <${Ze} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${oa(a).map(([i,c])=>s`<tr><td class="muted">${i}</td><td>${c}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>_(C(t,{run:a.id}),{replace:!0})}>
            <${w} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${o}><${w} name="copy" size=${15} /> Copy the run id</button>
          ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
            <${w} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(i=>{let c=E("result",i.check);return s`<a class=${`check small tone-${c.tone}`} href=${C(i.group)} data-tip=${i.statement}>
              <${w} name=${c.icon} size=${14} />${i.group==="."?"own proposal":i.group}
              ${i.verdict?s`<${L} spec=${E("verdict",i.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function aa({run:e,progress:t}){let{epoch:n,total:a,fraction:o,steps_per_epoch:i}=t,c=e.status==="running"&&o!==null&&i&&e.steps_per_s?xe((1-o)*a*i/e.steps_per_s):null;return s`<span>epoch <b>${n}</b>${a?` of ${a}`:""}${o===null?"":` \xB7 ${Math.round(o*100)} % through`}${c?` \xB7 about ${c} left`:""}</span>`}function os({path:e}){let t=k(kt(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([i,c])=>`${gt(i)} ${j(c)}`).join(", "),a=ne(e.split("/").pop()??""),o=`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}${n?` (${n})`:""}`;return s`<span data-tip=${o}>
    best <b>${t.label??gt(`metric.${t.metric}.${t.stat}`)} ${j(t.value)}</b>
    ${a?null:s` · <a href=${de(t.run)}>${t.name}</a>`}
  </span>`}function oa(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var Nt=80;function rs({node:e}){let t=Z("main"),n=Z(e.data?.keys?"keys":""),a=e.props.mode==="run",o=e.props.title??(a?"Config":"Hyperparameters");return s`<${Be} id=${`config:${e.id}`} title=${o} open=${e.props.open} result=${t}>
    ${t.data?a?s`<${et} config=${t.data.config} varying=${He(n.data)} />`:s`<${ra} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function ra({rows:e}){let t=new Set(He({config:{rows:e}})),n=e.filter(([a])=>t.has(a.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([a,,o])=>{let i=Array.isArray(o)?o.map(j).join(", "):`${j(o.min)} \u2026 ${j(o.max)} \xB7 ${o.distinct} values`;return s`<tr><td data-tip=${a}>${a.replace(/^config\./,"")}</td>
      <td data-tip=${i.length>Nt?i:void 0}>${i.length>Nt?`${i.slice(0,Nt-1)}\u2026`:i}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var is=15e3;function ls({node:e}){let t=J(U),n=ie(),[a,o]=Qt(),i=e.props.code,c=k(o&&i?{method:"code",params:i,scope:null}:null),[r,l]=y(null),[u,f]=y(120),[d,h]=y({error:null,warnings:[]}),$=x=>{ue&&console.error(`[block ${e.id}] ${x}`),h(m=>({...m,error:x}))},g=O(()=>{});T(()=>{if(!r)return;let x=!0;Le.n++;let m=()=>{x&&Le.n--,x=!1};g.current=m;let p=setTimeout(()=>{x&&$(`no first render within ${is/1e3} s`),m()},is);return()=>{clearTimeout(p),m()}},[r]),T(()=>{let x=r?.contentWindow;if(!x||c.status!=="ready")return;let m=D=>x.postMessage(D,"*"),p=new Map,b=new un,H=D=>{if(D.source!==x)return;let S=D.data;switch(S.type){case"hello":m({type:"init",init:{id:e.id,code:c.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:Zt.value,pair:qe.value,colormaps:We.value,prefs:bt(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!ln.has(S.call.method)){m({type:"result",id:S.id,result:{status:"error",data:null,error:`${S.call.method} is not available in a custom block`,refreshing:!1}});break}p.get(S.id)?.(),p.set(S.id,Kt(S.call,re=>m({type:"result",id:S.id,result:re})));break;case"unsub":p.get(S.id)?.(),p.delete(S.id);break;case"navigate":S.url.startsWith("/")&&_(S.url);break;case"height":b.accept(performance.now())?f(Math.max(40,S.height)):B("its height keeps changing, so it is fixed at its last height");break;case"ready":h(re=>({...re,blank:S.blank,overflow:S.overflow})),g.current();break;case"warn":B(S.message);break;case"hover":$t.set(S.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(S.prefs)&&A.set(S.prefs);break;case"download":case"snapshot":S.href?cn(S.href,S.name)?performance.now()-G>1e3&&(G=performance.now(),ze().download(S.href,S.name)):B(`a download of ${S.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":ze().figure(S.spec,S.name).catch(re=>B(`the PDF failed: ${re.message}`));break;case"expand":dn(S.node)&&ze().expand(S.node,t);break;case"error":$(S.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,M)),g.current();break;default:break}},B=D=>{ue&&console.warn(`[block ${e.id}] ${D}`),h(S=>S.warnings.includes(D)?S:{...S,warnings:[...S.warnings,D]})},G=-1/0,A=bt(t.path),Y=$t.subscribe(D=>m({type:"hover",run:D})),R=A.subscribe(D=>m({type:"prefs",prefs:D}));return addEventListener("message",H),m({type:"ping"}),()=>{Y(),R(),removeEventListener("message",H);for(let D of p.values())D()}},[c.status,c.data?.code,r]),T(()=>{let x={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};r?.contentWindow?.postMessage(x,"*")},[t.names,t.colors,t.metrics,r]),T(()=>{n&&r?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let M=typeof i=="object"?i.path??i.block:String(i??"");en(e.id,{png:()=>r?.contentWindow?.postMessage({type:"snapshot"},"*")});let v=o&&c.status==="ready"&&!d.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${v?s`<span class="chart-tools">
            <${W} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>r?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${W} icon="x" label="Close (Esc)" onClick=${()=>Oe.set(null)} />`:s`<${W} icon="maximize" label="Expand" onClick=${()=>ze().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${se} caption=${e.props.expanded?void 0:e.props.caption} result=${c}>
      ${d.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${M})</span>
            <pre class="code">${d.error}</pre>
          </div>`:null}
      ${d.warnings.map(x=>s`<${z} kind="warning">${x}<//>`)}
      ${v?s`<div class="custom-frame" data-frame-blank=${d.blank?"1":void 0} data-frame-overflow=${d.overflow?"1":void 0}>
            <iframe key=${c.data.code} ref=${l} sandbox="allow-scripts" ...${ia()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function ia(){if(!!1)return{src:At("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function cs({node:e}){let t=Z("main"),n=J(U),a=t.data?.entries??[];return s`<${se} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(o=>s`<figure key=${`${o.run}/${o.path}`}>
          <img src=${Ht(Re(o.run,n.path),o.path)} alt=${o.caption??e.props.title} loading=${Ie?"eager":"lazy"} />
          <figcaption class="small">step ${ke(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function ds({node:e}){let t=Z("main"),n=t.data?.entries??[];return s`<${se} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${z}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${ke(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function us({node:e}){let n=`section.${J(U).path}:${e.id}`,[a,o]=y(()=>Ie||he(n,e.props.open!==!1)),i=()=>{ge(n,!a),o(!a)},c=s`${(e.children??[]).map(u=>s`<${oe} key=${u.id} node=${u} />`)}`,r=J(Je);if(!e.props.title)return s`<div class="stack">${c}</div>`;let l=r===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${a} aria-label=${l?`${a?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${l?`${a?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${i}>
      <${w} name=${a?"chevron-down":"chevron-right"} size=${16} />${l?null:e.props.title}
    </button>
    ${a?s`<div class="stack">${c}</div>`:null}
  </div>`}function ms({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${oe} key=${n.id} node=${n} />`)}
  </div>`}function Pt({node:e,after:t}){let n=J(U),a=Se(n.path),o=e.props.min_width??320,i=e.props.columns,c=i?`grid-template-columns: repeat(${i}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${o}px, 100%), 1fr))`,r=e.children??[],l=r.filter(d=>a.removed.includes(d.id)).map(d=>d.id),u=rn(r.filter(d=>!l.includes(d.id)),a.order[e.id]),f=(d,h)=>{let $=u.map(g=>g.id).filter(g=>g!==d);$.splice($.indexOf(h),0,d),an(n.path,e.id,$)};return s`<div class="grid" style=${c}>
    ${u.map(d=>s`<${la} key=${d.id} node=${d} path=${n.path} span=${a.spans[d.id]??d.props.span??1}
      columns=${i} onDrop=${h=>h!==d.id&&f(h,d.id)} />`)}
    ${t??null}
    ${l.length?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ke(n.path,l)}>${l.length} hidden · show</button></div>`:null}
  </div>`}var Dt=[1,2,"full"];function la(e){let[t,n]=y(!1),a=Dt[(Dt.indexOf(e.span)+1)%Dt.length],o=i=>i==="full"?"full width":`${i} column${i===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${i=>{i.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${i=>{i.preventDefault(),n(!1),e.onDrop(i.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${i=>i.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${w} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${o(e.span)}; click for ${o(a)}`}
        aria-label=${`Width ${o(e.span)}`} onClick=${()=>on(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${oe} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function _t({root:e}){let t=J(U),n=Se(t.path),a=k({method:"keys",params:{from:t.path},scope:t.path}).data,o=e.props.template;if(!o||!1)return null;let i=new Set(n.removed),c=new Set([...t.charted].filter(([$])=>!i.has($)).flatMap(([,$])=>$)),r=n.added.filter($=>!c.has($)).map($=>({block:"line",id:`added-${$}`,props:{y:$},data:{main:{...o,params:{...o.params,y:[$]}}}})),l=new Set([...c,...r.filter($=>!i.has($.id)).map($=>$.props.y)]),u=(a?.metrics?.rows??[]).map($=>$[0]).filter($=>!l.has($));if(!a||!(u.length||r.length))return null;let f=$=>[...t.charted].find(([g,M])=>i.has(g)&&M.includes($))?.[0]??r.find(g=>i.has(g.id)&&g.props.y===$)?.id,d=$=>{let g=f($);g?Ke(t.path,[g]):tt(t.path,M=>({added:[...M.added,$]}))},h=u.length?s`<div class="add-chart">
        <span class="add-chart-label"><${w} name="plus" size=${16} /> Add a chart</span>
        <${Qe} single options=${u} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([$])=>d($)} />
      </div>`:null;return s`<${I}><${Pt} node=${{block:"grid",id:"added",props:{},children:r}} after=${h} /><//>`}function ps({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,o]=y(()=>t.find(r=>r.id===n())?.id??t[0]?.id),i=r=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(r)}`),o(r)},c=t.find(r=>r.id===a)??t[0];return Ie?s`<div class="stack">${t.map(r=>s`<${oe} key=${r.id} node=${r} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(r=>s`<button type="button" role="tab" id=${`tab-${r.id}`} aria-selected=${r.id===c?.id}
          aria-controls=${`panel-${r.id}`} onClick=${()=>i(r.id)}>${r.props.title??r.id}</button>`)}
    </div>
    ${c?s`<div class="stack" role="tabpanel" id=${`panel-${c.id}`} aria-labelledby=${`tab-${c.id}`}>
          ${(c.children??[]).map(r=>s`<${oe} key=${r.id} node=${r} />`)}
        </div>`:null}
  </div>`}var $s={section:us,row:ms,grid:Pt,line:vn,table:xn,stat:kn,images:cs,text:ds,proposal:qn,note:ns,output:es,config:rs,memory:Xn,groups:Yn,notes:Jn,tabs:ps,scatter:bn,bar:yn,histogram:wn,data_table:$n,timeline:fn,custom:ls,markdown:ts},ca=new Set(["line","scatter","bar","histogram"]);function oe({node:e}){return ca.has(e.block)?s`<${da} node=${e} />`:s`<${yt} node=${e} blocks=${$s} />`}function da({node:e}){let t=J(U);return Se(t.path).removed.includes(e.id)?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ke(t.path,[e.id])}>1 hidden · show</button></div>`:s`<${yt} node=${e} blocks=${$s} />`}function fs(e,t){let n=e.split(`
`),a=t.split(`
`),o=n.length,i=a.length,c=Array.from({length:o+1},()=>new Uint32Array(i+1));for(let f=o-1;f>=0;f--)for(let d=i-1;d>=0;d--)c[f][d]=n[f]===a[d]?c[f+1][d+1]+1:Math.max(c[f+1][d],c[f][d+1]);let r=[],l=0,u=0;for(;l<o&&u<i;)n[l]===a[u]?(r.push({kind:"same",text:n[l]}),l++,u++):c[l+1][u]>=c[l][u+1]?r.push({kind:"removed",text:n[l++]}):r.push({kind:"added",text:a[u++]});for(;l<o;)r.push({kind:"removed",text:n[l++]});for(;u<i;)r.push({kind:"added",text:a[u++]});return r}function hs(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let o=a;for(;o<e.length&&e[o].kind==="same";)o++;let i=a===0?0:t,c=o===e.length?0:t;o-a>i+c+1?n.push(...e.slice(a,a+i),{kind:"skip",count:o-a-i-c},...e.slice(o-c,o)):n.push(...e.slice(a,o)),a=o}return n}var Lt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function gs(e){if(Lt[e.block])return Lt[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(o=>Lt[o.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function ut(e){let t=k(Ue(e.path)),n=ie(),a=P(t.data),o=_e(()=>Ye(a.map(d=>d["run.id"]),n),[t.data,n]),i=_e(()=>new Map(a.map(d=>[d["run.id"],d["run.name"]??d["run.id"]])),[t.data]),c=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${c}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${I} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let r=e.view.view,l={path:e.path,colors:o,names:i,metrics:e.view.metrics??{},charted:Rt(r)};if(e.plain)return s`<div class=${c}><${U.Provider} value=${l}><${oe} node=${r} /><//></div>`;let u=r.block==="section"&&!r.props.title?r.children??[]:[r],f=u.map(d=>Rt(d).size>0).lastIndexOf(!0);return s`<div class=${c}>${e.before}
    <${U.Provider} value=${l}>
      ${u.map((d,h)=>{let $=gs(d);return s`<${I} key=${d.id} label=${$}><${Je.Provider} value=${$}><${oe} node=${d} /><//><//>
          ${h===f?s`<${_t} root=${r} />`:null}`})}
      ${f===-1?s`<${_t} root=${r} />`:null}
    <//>
  </div>`}function Rt(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])Rt(n,t);return t}function vs(e){if(null)return s`<div class="view-source small"><${w} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=N(q),a=n.page==="group"&&n.version,o=t.versions?s`<a href=${C(e.path,{history:!0})}><${w} name="history" size=${14} /> history (${t.versions})</a>`:null,i;switch(t.source){case"draft":i=s`draft <b>${t.draft}</b>`;break;case"view":i=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${F(ve(t.version))} by ${t.author??"unknown"}`;break;default:i=s`the built-in view`}return s`<div class="view-source small">
    <${w} name="layout" size=${14} /><span>${i}</span>
    ${a?s`<a href=${C(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!a?s`<${ua} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${ma} path=${e.path} />
        <${pa} path=${e.path} view=${t} />`}
  </div>`}function ua(e){let[t,n]=y(null),a=e.outdated.map(i=>i.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Dn(e.path)}catch(i){n(i.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${w} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function ma(e){let[t,n]=y(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Me.set(await st(e.path,null,""))}catch(o){n(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${w} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function pa(e){let t=Se(e.path),n=sn(t),[a,o]=y(!1),[i,c]=y(e.view.title??""),[r,l]=y(e.view.finding??""),[u,f]=y(null),[d,h]=y(!1);if(!n&&!a)return null;let $=async g=>{g.preventDefault(),h(!0),f(null);try{let M={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans};await K("save_view",{path:e.path,prefs:M,title:i,finding:r}),tt(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{}})),Ee(v=>["view","view_history","summary"].includes(v.method)&&v.scope===e.path),o(!1)}catch(M){f(M.message)}finally{h(!1)}};return a?s`<form class="save-form" onSubmit=${$}>
    <${Ae} label="Title"><input value=${i} onInput=${g=>c(g.target.value)} /><//>
    <${Ae} label="Finding"><input value=${r} placeholder="the key result in one sentence"
        onInput=${g=>l(g.target.value)} /><//>
    <div class="save-actions">
      <${ae} type="submit" icon=${d?"hourglass":"save"} disabled=${d}>${d?"Saving\u2026":"Save as view"}<//>
      <${ae} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
      ${u?s`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:s`<${ae} icon="save" class="save-view" onClick=${()=>o(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function bs(e){let t=k(Bn(e.path)),n=t.data?.entries??[],[a,o]=y(null),i=a??n.slice(0,2).map(r=>r.version).reverse(),c=r=>{let l=i.includes(r)?i.filter(u=>u!==r):[...i,r].slice(-2);o(l.sort())};return t.status==="error"?s`<${z} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${w} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((r,l)=>s`<li key=${r.version} class=${i.includes(r.version)?"picked":""}>
          <label><input type="checkbox" checked=${i.includes(r.version)} onChange=${()=>c(r.version)} />
            <span class="num muted" data-tip=${r.version}>${F(r.time)}</span>
            <b>${r.title??"untitled"}</b><span class="muted">${r.author??""}</span>
            ${r.message?s`<span>${r.message}</span>`:null}</label>
          <a href=${l===0?C(e.path):C(e.path,{version:r.version})}
            onClick=${u=>{u.preventDefault(),_(l===0?C(e.path):C(e.path,{version:r.version}))}}>${l===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${i.length===2?s`<${$a} path=${e.path} a=${i[0]} b=${i[1]} />`:null}
  </section>`}function $a(e){let t=r=>({method:"view_show",params:{group:e.path,version:r},scope:e.path}),n=k(t(e.a)).data,a=k(t(e.b)).data,o=k(pe(e.path,e.a)).data,i=k(pe(e.path,e.b)).data,c=n&&a?hs(fs(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${F(ve(e.a))} to ${F(ve(e.b))}</h3>
    <pre class="diff code">${c.map(r=>r.kind==="skip"?s`<div class="diff-skip">⋯ ${r.count} unchanged lines</div>`:s`<div class=${`diff-${r.kind}`}>${r.kind==="added"?"+ ":r.kind==="removed"?"\u2212 ":"  "}${r.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${o?.title??e.a}</h3><${ut} path=${e.path} view=${o} plain /></div>
      <div><h3 class="block-title heading">${i?.title??e.b}</h3><${ut} path=${e.path} view=${i} plain /></div>
    </div>
  </div>`}function ys(e){return An(e.path),e.history?s`<div class="page"><div class="sections">
      <${I} label=${ws(e.path)}><${Mt} path=${e.path} /><//>
      <${I} label="history"><${bs} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${fa} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function fa(e){let t=k(pe(e.path,e.version,e.draft));T(()=>{t.status==="ready"&&requestAnimationFrame(Vt)},[t.status==="ready"]);let n=s`
    <${I} label=${ws(e.path)}>
      <${Mt} path=${e.path} finding=${t.data?.finding} />
      ${t.data?s`<${vs} path=${e.path} view=${t.data} />`:null}
    <//>
    ${ne(e.path.split("/").pop()??"")?null:s`<${as} path=${e.path} />`}`;return t.status==="error"?s`<div class="sections">${n}
      <${I} label="view">
        ${ha(e.path,t.error)?s`<${z} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${z} kind="error">${t.error}<//>`}
      <//>
    </div>`:s`<${ut} path=${e.path} view=${t.data} before=${n} />`}function ws(e){return ne(e.split("/").pop()??"")?"run":"group"}function ha(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function ks(e){T(()=>{Ce(pe(e.id)).then(n=>_(C(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=k(pe(e.id));return t.status==="error"?s`<div class="page"><${z} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var ga={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},It=20,Pe=-1,va=[["day",86400],["week",7*86400],["month",30*86400]];function Ss(e){let t=P(k(le()).data).map(r=>r.path),n=k({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=k({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});je("Timeline",P(n.data).filter(r=>r["run.status"]==="running").length);let o=Date.now()/1e3,i=P(n.data).filter(r=>r["run.created_at"]).map((r,l)=>({id:r["run.id"],name:r["run.name"]??r["run.id"],group:r["run.group"],status:r["run.status"],start:Date.parse(r["run.created_at"])/1e3,end:r["run.ended_at"]?Date.parse(r["run.ended_at"])/1e3:o,lane:l})),c=(a.data?.entries??[]).map(r=>({id:r.id,type:r.type,group:r.group,description:r.description,t:Date.parse(ve(r.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${I} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Ae} label="Group" inline>
          <select value=${e.from} onChange=${r=>_(Ve(r.target.value),{replace:!0})}>
            ${t.map(r=>s`<option value=${r}>${r==="."?"everything":r}</option>`)}
          </select><//>
        <span class="muted small">${i.length} runs · ${c.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${I} label="runs">
      ${n.status==="error"?s`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${ba} bars=${i} marks=${c} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function ba(e){let t=ie(),n=O(null),a=[...e.bars.flatMap(v=>[v.start,v.end]),...e.marks.map(v=>v.t)],o=a.length?xs(Math.min(...a),Math.max(...a)):xs(Date.now()/1e3-86400,Date.now()/1e3),[i,c]=y(o),r=e.bars.length,l=Math.min(900,Math.max(160,(r+1.5)*It+40)),f=hn(n,gn,t?(v=>{let x=mn(i[0],i[1]),m=b=>v.colors[ga[b]??"muted"],p=b=>v.colors[b==="verdict"?"good":b==="decision"?"accent":b==="question"?"warn":"muted"];return{style:Jt(v),height:l,x:{range:i,log:!1,format:b=>pn(b,x.step),label:"",splits:x.at},y:{range:[Pe-.8,r+.5],log:!1,reverse:!0,label:"",size:150,splits:r<=40?[Pe,...e.bars.map(b=>b.lane)]:[Pe],format:b=>b===Pe?"notes":Sa(e.bars[Math.round(b)]?.name??"")},draw:({ctx:b,x:H,y:B,px:G,focused:A})=>{let Y=It*.62*G;for(let R of e.bars){let D=H(R.start),S=Math.max(3*G,H(R.end)-D);b.fillStyle=A!==null&&A!==R.id?Yt(m(R.status),.35):m(R.status),b.beginPath(),b.roundRect(D,B(R.lane)-Y/2,S,Y,3*G),b.fill()}for(let R of e.marks){let D=H(R.t),S=B(Pe),re=(A===R.id?6:4.5)*G;b.fillStyle=p(R.type),b.beginPath(),b.moveTo(D,S-re),b.lineTo(D+re,S),b.lineTo(D,S+re),b.lineTo(D-re,S),b.closePath(),b.fill()}},hit:(b,H,B,G)=>{if(Math.abs(H-G(Pe))<It/2){let R=xa(e.marks,D=>Math.abs(B(D.t)-b),8);return R?{key:R.id,rows:wa(R)}:null}let A=Math.round((H-G(0))/(G(1)-G(0))),Y=e.bars.find(R=>R.lane===A&&B(R.start)-3<=b&&b<=Math.max(B(R.end),B(R.start)+3)+3);return Y?{key:Y.id,rows:ya(Y)}:null},onClick:b=>{let H=e.marks.find(B=>B.id===b);H?_(C(H.group,{drawer:!0})):_(de(b))}}})(t):null,[i,e.bars,e.marks],t),d=v=>{if(!f.current)return;v.preventDefault();let x=f.current.xAt(v.clientX),m=Math.exp(v.deltaY*.0015);c(([p,b])=>Ot([x-(x-p)*m,x+(b-x)*m],o))},h=O(null),$=v=>h.current={x:v.clientX,range:i},g=v=>{if(!h.current||!f.current||!(v.buttons&1))return;let x=(v.clientX-h.current.x)*f.current.xPerPixel(),[m,p]=h.current.range;Math.abs(v.clientX-h.current.x)>3&&c(Ot([m-x,p-x],o))},M=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${va.map(([v,x])=>s`<button type="button" role="radio" aria-checked=${Math.abs(i[1]-i[0]-x)<1}
          onClick=${()=>c(Ot([M-x,M+x*.02],[Math.min(o[0],M-x),o[1]]))}>last ${v}</button>`)}
      <button type="button" role="radio" aria-checked=${i[0]===o[0]&&i[1]===o[1]} onClick=${()=>c(o)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${l}px`}
      onWheel=${d} onPointerDown=${$} onPointerMove=${g} onPointerUp=${()=>h.current=null}></div>
    <p class="muted small">${ka(t)}</p>
  </div>`}function ya(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:F(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:xe(e.end-e.start),color:null}]}function wa(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:F(new Date(e.t*1e3).toISOString()),color:null}]}function ka(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function xa(e,t,n){let a=null,o=n;for(let i of e){let c=t(i);c<o&&([a,o]=[i,c])}return a}function xs(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Ot([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),o=Math.max(n[0],Math.min(e,n[1]-a));return[o,o+a]}function Sa(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function Cs(){let e=N(Oe),t=O(null);if(T(()=>{let o=t.current;if(!o||!e)return;o.showModal();let i=()=>Oe.set(null);return o.addEventListener("close",i),()=>o.removeEventListener("close",i)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${U.Provider} value=${e.view}><${oe} node=${n} /><//>
  </dialog>`}function Es(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let o=a.indexOf(n);if(o>=0)return 100-Math.min(o,50)-a.length/100;let i=0,c=0;for(let r of a)if(r===n[i]?i++:i>0&&c++,i===n.length)return 40-Math.min(c,39);return 0}function Ms(e){let[t,n]=y(e.query),[a,o]=y(0),i=O(null),c=P(k(le()).data),r=P(k(ot()).data);T(()=>{let m=i.current;m.showModal();let p=()=>ee.set(null);m.addEventListener("close",p);let b=!1,H=A=>{let Y=m.getBoundingClientRect();return A.clientX<Y.left||A.clientX>Y.right||A.clientY<Y.top||A.clientY>Y.bottom},B=A=>b=H(A),G=A=>b&&H(A)&&m.close();return"closedBy"in HTMLDialogElement.prototype||(m.addEventListener("pointerdown",B),m.addEventListener("pointerup",G)),()=>{m.removeEventListener("close",p),m.removeEventListener("pointerdown",B),m.removeEventListener("pointerup",G)}},[]);let l=()=>i.current?.close(),u=m=>()=>_(m),f=q.value,d=f.page==="group"?f.path:".",h=(m,p,b,H)=>({section:"Commands",label:m,detail:p,sym:{icon:b,tone:"muted",label:m},run:H}),g=[...c.map(m=>({section:"Groups",label:m.path==="."?"local":m.path,detail:`${m.runs} runs${m.proposal?` \xB7 ${m.proposal}`:""}`,sym:E("research",m.status),run:u(C(m.path))})),...r.map(m=>({section:"Runs",label:m["run.name"]??m["run.id"],detail:`${m["run.status"]} \xB7 ${m["run.path"]}`,sym:E("run",m["run.status"]),run:u(C(m["run.path"]))})),h("Theme: light","","sun",()=>Xe("light")),h("Theme: dark","","moon",()=>Xe("dark")),h("Theme: follow the system","","monitor",()=>Xe("system")),h("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),h("Show notes and timeline","i","file-text",u(C(d,{drawer:!0}))),h("Show or hide the sidebar","\u2318B","panel-left",()=>Q.set(!Q.value)),h(te.value?"Resume live updates":"Pause live updates","p",te.value?"play":"pause",()=>te.set(!te.value)),h("Keyboard shortcuts","?","keyboard",()=>$e.set(!0)),h("Settings","","settings",u("/settings/appearance"))].map(m=>({it:m,s:Math.max(Es(t,m.label),Es(t,m.detail)*.5)})).filter(m=>m.s>0).sort((m,p)=>p.s-m.s||Ts(m.it.section)-Ts(p.it.section)).slice(0,60).map(m=>m.it),M=m=>{m&&(l(),m.run())},v=m=>{if(m.key==="ArrowDown")o(Math.min(g.length-1,a+1));else if(m.key==="ArrowUp")o(Math.max(0,a-1));else if(m.key==="Enter")M(g[a]);else return;m.preventDefault()},x="";return s`<dialog class="sheet" ref=${i} aria-label="Search" closedby="any">
    <div class="palette-input"><${w} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${g[a]?`pal-${a}`:void 0}
        onInput=${m=>{n(m.target.value),o(0)}} onKeyDown=${v} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${g.map((m,p)=>{let b=m.section!==x&&!t?x=m.section:null;return s`${b?s`<li class="palette-head small" role="presentation">${b}</li>`:null}
          <li id=${`pal-${p}`} class="item" role="option" aria-selected=${p===a}
              onMouseMove=${()=>o(p)} onClick=${()=>M(m)}>
            <${L} spec=${m.sym} /><span class="label">${m.label}</span><span class="detail small">${m.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function Ts(e){return["Groups","Runs","Commands"].indexOf(e)}function mt(e,t=[]){let n=new Map,a=(r,l={})=>({path:r,name:r==="."?"local":r.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let r of e)n.set(r.path,a(r.path,r));(t.length===0||t.some(r=>r.name==="local"))&&!n.has(".")&&n.set(".",a("."));for(let r of t){let l=r.name==="local"?".":r.name;n.has(l)||n.set(l,a(l)),Object.assign(n.get(l),{state:r.state,error:r.error})}for(let r of n.values()){if(V(r.path))continue;let l=r.path.lastIndexOf("/"),u=l<0?".":r.path.slice(0,l);(n.get(u)??n.get(we(r.path))??n.get(".")).children.push(r)}for(let r of n.values())r.children.sort((l,u)=>l.name.localeCompare(u.name));let i=[...n.values()].filter(r=>r.path!=="."&&V(r.path)).sort((r,l)=>r.name.localeCompare(l.name)),c=n.get(".");return c?[c,...i]:i}function Ns(e,t,n,a=new Set){let o=[],i=n.toLowerCase(),c=r=>{(!i||r.path.toLowerCase().includes(i)||Ds(r,i))&&(o.push(r),(i||(V(r.path)?!a.has(r.path):t.has(r.path)))&&r.children.forEach(c))};return e.forEach(c),o}function Ds(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Ds(n,t))}function Ps(e,t){if(V(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),o=i=>i.path===a?i:i.children.map(o).find(c=>c)??null;return e.map(o).find(i=>i)?.children??[]}function _s(e){return V(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Ls(){let e=N(q),t=k(le()),[n,a]=y(()=>new Set(he("open",[]))),[o,i]=y(()=>new Set(he("closed-hosts",[]))),[c,r]=y(""),l=O(null),u=e.page==="group"?e.path:null,f=mt(P(t.data),t.data?.meta?.sources??[]),d=Ns(f,Ta(n,u),c,o),h=v=>V(v)?!o.has(v):n.has(v),$=(v,x)=>{let m=x??!h(v);if(V(v)){let b=new Set(o);m?b.delete(v):b.add(v),ge("closed-hosts",[...b]),i(b);return}let p=new Set(n);m?p.add(v):p.delete(v),ge("open",[...p]),a(p)},g=O(u);return T(()=>{u!==g.current&&u&&!V(u)&&o.has(we(u))&&$(we(u),!0),g.current=u},[u]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${w} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${c} aria-label="Filter groups"
        onInput=${v=>r(v.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${v=>{let x=[...l.current?.querySelectorAll("a.tree-item")??[]],m=x.indexOf(document.activeElement),p=d[m];switch(v.key){case"ArrowDown":x[Math.min(x.length-1,m+1)]?.focus();break;case"ArrowUp":x[Math.max(0,m-1)]?.focus();break;case"ArrowRight":p?.children.length&&$(p.path,!0);break;case"ArrowLeft":p?.children.length&&h(p.path)?$(p.path,!1):p&&x[d.findIndex(b=>b.path===Ea(p.path))]?.focus();break;default:return}v.preventDefault()}} role="tree">
      ${d.map(v=>s`<${Ca} key=${v.path} node=${v} current=${v.path===u}
        open=${h(v.path)||!!c} onToggle=${()=>$(v.path)} />`)}
    </div>
  </nav>`}function Ca(e){let t=e.node,n=()=>Fe(t.path),a=t.children.length>0,o=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${V(t.path)?" source-root":""}`} href=${C(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${8+_s(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${i=>{i.metaKey||i.ctrlKey||(i.preventDefault(),_(C(t.path)))}}>
    <span class="twisty" onClick=${i=>{i.preventDefault(),i.stopPropagation(),e.onToggle()}}>
      ${a?s`<${w} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${V(t.path)?s`<${L} size=${14} spec=${{icon:o?"cloud-off":"server",tone:"muted",label:o?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${L} spec=${E("run","running")} size=${14} />`:null}
      ${t.failed?s`<${L} spec=${{...E("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Ea(e){if(V(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function Ta(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let o=1;o<a.length;o++)n.add(a.slice(0,o).join("/"));return n}function Is(){let e=N(q),t=N(Q),n=N(ee),a=N($e),o=O(null);T(()=>Gt(()=>o.current),[]),T(()=>(addEventListener("keydown",Rs),()=>removeEventListener("keydown",Rs)),[]);let i=e.page==="group"&&e.drawer,c;switch(e.page){case"group":c=s`<${ys} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":c=s`<${ks} id=${e.id} />`;break;case"settings":c=s`<${Fn} />`;break;case"timeline":c=s`<${Ss} key=${e.from} from=${e.from} />`;break;default:c=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return ue||!1?s`<main class="main render-main" ref=${o}>${c}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${i?" with-drawer":""}`}>
    <${Gn} />
    ${t?s`<${Ls} />`:null}
    <main class="main" ref=${o}>${c}</main>
    ${i?s`<${ss} path=${e.path} run=${e.run} />`:null}
    <${Vn} />
    ${n!==null?s`<${Ms} query=${n} />`:null}
    ${a?s`<${Na} />`:null}
    <${Cs} />
  </div>`}function Rs(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),ee.set(ee.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Q.set(!Q.value);return}if(e.key==="Escape"){if(ee.value!==null||$e.value)return;let a=q.value;return a.page==="group"&&a.run?_(C(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?_(C(a.path),{replace:!0}):void 0}if(t||e.altKey||Kn(e)||ee.value!==null||$e.value)return;let n=q.value;switch(e.key){case"/":e.preventDefault(),ee.set("");break;case"?":$e.set(!$e.value);break;case"p":te.set(!te.value);break;case"i":n.page==="group"&&_(C(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Q.set(!Q.value);break;case"[":case"]":n.page==="group"&&Ma(n.path,e.key==="]"?1:-1);break}}async function Ma(e,t){let n=await Ce(le()),a=Ps(mt(P(n),n?.meta?.sources??[]),e),o=a.findIndex(c=>c.path===e),i=a[o+t];i&&_(C(i.path))}function Na(){let e=O(null);return T(()=>{let t=e.current;t.showModal();let n=()=>$e.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${it.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ae} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Wt();if(ue){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(me.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Le.n,qt&&tn()}Sn();var Da=K("meta").then(e=>(ue&&(e={...e,settings:{...e.settings,theme_mode:me.value}}),lt(e),e));!ue&&!!1&&jt(async()=>{let[e,t]=await Promise.all([Da,K("meta")]);e.bundle!==t.bundle?location.reload():lt(t)});zt(s`<${Is} />`,document.getElementById("app"));
