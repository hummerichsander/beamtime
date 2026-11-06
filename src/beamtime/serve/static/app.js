import{$ as re,$a as hn,A as Pt,Aa as qt,B as Ot,Ba as ft,C as Se,Ca as Xe,D as le,Da as Ye,E as S,Ea as Xt,F as Ke,Fa as Yt,G as ce,Ga as Jt,H as _e,Ha as Zt,I as be,Ia as Qt,J as G,K as V,L as It,La as en,Ma as tn,N as D,Na as nn,O as zt,Oa as sn,P as Bt,Pa as an,Q as de,Qa as rn,R as Le,Ra as on,S as At,Sa as ln,T as Ue,U as dt,Ua as cn,V as ue,Va as dn,W as Ft,Wa as un,X as ut,Xa as mn,Y as Fe,Ya as pn,Z as X,Za as $n,_ as Y,_a as fn,aa as je,ba as jt,c as Mt,ca as Re,d as s,da as Pe,e as g,f as E,fa as Gt,g as Nt,ga as Wt,h as O,ha as b,i as Ne,ia as L,j as ie,ja as Ge,ka as te,la as I,m as ve,ma as P,n as M,na as Oe,o as we,oa as W,p as ke,pa as Vt,qa as z,ra as ne,s as K,sa as Ie,t as De,ta as mt,u as xe,ua as We,v as ct,va as Ve,w as y,wa as T,x as Lt,xa as $t,y as ee,ya as ze,z as Rt,za as qe}from"./chunks/chunk-6BY5GYEI.js";import{a as Dt,b as _t}from"./chunks/chunk-O2K4N3UR.js";import{e as Ht,i as Kt,j as Ut,k as F,n as he,o as ye,p as Ce,q as U,r as pt}from"./chunks/chunk-KRR2HWC7.js";import"./chunks/chunk-VC46IEJQ.js";function Ee(e,t){Se(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var ht=["notes","timeline","groups","check","card","memory_show","status"];async function Je(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Ee(e.group,ht)}async function gn(e,t,n,a){await K("note_add",{group:e,type:t,description:n,body:a}),Ee(e,ht)}async function vn(e,t){await K("memory_update",{group:e,body:t}),Ee(e,["memory_show","status"])}async function bn(e,t){let n=await K("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await K("proposal_set",{group:e,proposal:{...a,statement:t}}),Ee(e,["groups","proposal_show","check","summary"])}async function yn(e){await K("note_rm",{note:e.id}),Ee(e.group,ht)}async function wn(e,t,n){await K("name",{run:e,name:n}),Ee(t,["card","runs","groups","summary","series"])}async function Ze(e,t,n){let a=await K("view_text",{path:e,id:t,text:n});return Se(r=>["view","view_history"].includes(r.method)&&r.scope===e),a.id}async function kn(e){await K("view_upgrade",{group:e}),Se(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Te=new ve(null);async function xn(e,t){return await K("set",{key:e,value:t}),K("meta")}var J=new ve(we("sidebar",!0)),Z=new ve(null),me=new ve(!1),pe=new ve(null);J.subscribe(e=>ke("sidebar",e));var Sn=we("visit",Date.now());ke("visit",Date.now());function Cn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var Qe=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Ts=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function et(e){pe.set(e),Ue.set(e.theme),e.settings?.theme_mode&&ue.set(e.settings.theme_mode),ut()}var En=0;async function gt(e,t){let n=++En;e==="theme_mode"&&(ue.set(t),ut());let a=await xn(e,t);n===En&&et(a)}function Tn(){let e=M(ue),t=re(),n=M(pe),[a,r]=g(null);E(()=>{document.title="Settings \xB7 Beamtime"},[]);let o=(c,u)=>{r(null),gt(c,u).catch(m=>r(m.message))},l=n?.settings??{},i=(c,u,m)=>s`
    <label class="field-label small" for=${`setting-${c}`}>${u}</label>
    <span class="input body">
      <select id=${`setting-${c}`} value=${l[c]} onChange=${p=>o(c,p.target.value)}>
        ${m.map(p=>s`<option value=${p}>${p}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${z} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${a?s`<${I} kind="error">${a}<//>`:null}
    <//>
    <${z} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Ts.map(([c,u,m])=>s`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>o("theme_mode",c)}>
            <${b} name=${u} size=${15} />${m}</button>`)}
        </div>
        ${i("theme","Theme",n?.themes??[])}
        ${i("colormap","Colormap",n?.colormaps?.sequential??[])}
        ${i("colormap_diverging","Diverging colormap",n?.colormaps?.diverging??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps color numeric groups and heatmaps.</p>
      ${(n?.theme?.problems??[]).map(c=>s`<${I} kind="warning">${c}<//>`)}
    <//>
    <${z} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${Ve} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${c=>o("figure_style",c)} />`:s`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${z} label="keyboard">
      <table class="kv">${Qe.map(([c,u])=>s`<tr><td><kbd class="small">${c}</kbd></td><td>${u}</td></tr>`)}</table>
    <//>
    <${z} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        <tr><td class="muted">log dir</td><td><code class="code">${n?.logdir}</code></td></tr>
      </table>
    <//>
  </div></div>`}var oe=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),$e=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),vt=e=>({method:"summary",params:{path:e},scope:e}),tt=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Mn=e=>({method:"check",params:{group:e},scope:e}),Nn=e=>({method:"proposal_show",params:{group:e},scope:e}),nt=(e,t)=>({method:"card",params:{run:_e(e,t)},scope:t}),Dn=(e,t)=>({method:"output",params:{run:_e(e,t),tail:30},scope:t}),Be=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),st=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),_n=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Ln=()=>({method:"status",params:{},scope:"."}),at=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ae(e){for(let t of[$e(e),tt(e),Be(e),vt(e)])ct(t);xe($e(e)).then(t=>{for(let n of Rn(t.view))ct(n)}).catch(()=>{})}function Rn(e){return e?[...Ms.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(Rn)]:[]}var Ms=new Set(["line","custom"]),Pn=e=>({method:"view_history",params:{group:e},scope:e});var On={system:"light",light:"dark",dark:"system"},Ns={system:"monitor",light:"sun",dark:"moon"};function In(){let e=M(pe),t=M(ue),n=M(J);return s`<header class="topbar">
    <${W} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>J.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>Z.set("")} aria-label="Search (⌘K)">
      <${b} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Ds} />
      <${W} icon=${Ns[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${On[t]})`}
        onClick=${()=>{gt("theme_mode",On[t])}} />
      <a class="icon-button" href=${Ke(V.value.page==="group"?V.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${b} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${b} name="settings" size=${16} /></a>
    </div>
  </header>`}function Ds(){let t=(y(oe()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${S(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${b} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${b} name="server" size=${15} /> local</span>`}function _s(e){let[t,n]=g(Date.now());return E(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function Ls(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function zn(){let e=M(Rt),t=M(ee),n=M(Pt),a=M(V),r=_s(5e3),o=y(Ln()).data,l=P(y(at()).data),i=M(pe),c=o?.daemon,u=o?.runs?.running??0,m=l.filter(_=>_["run.status"]==="failed"&&Ls(_["run.ended_at"])>Sn).length,p=o?.meta?.freshness,[v,C,x]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${U(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${x}><span class=${`live-dot ${v}`}></span>${C}</span>
    ${u?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>Z.set("running")}>
          <${b} name="circle-dot" size=${14} class="tone-accent" />${u} running</button>`:null}
    ${m?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>Z.set("failed")}>
          <${b} name="circle-x" size=${14} />${m} failed since your last visit</button>`:null}
    ${p?.behind?s`<span class="status-item warn-text" data-tip=${p.text}><${b} name="hourglass" size=${14} />${p.behind} runs behind</span>`:null}
    ${p?.damaged?.length?s`<span class="status-item warn-text" data-tip=${p.damaged.join(`
`)}><${b} name="triangle-alert" size=${14} />${p.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${b} name="activity" size=${14} />1 run selected</span>`:null}
    <${W} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ee.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var Bn=null;function rt(e){let t=O(null),[n,a]=g(null),[r,o]=g(!1),[l,i]=g(!1);E(()=>{let p=!0;return Bn??=import("./chunks/md-SW3VT2BQ.js"),Bn.then(v=>v.render(e.text??"")).then(v=>p&&a(v)),()=>{p=!1}},[e.text]),Nt(()=>{let p=t.current;if(!p||!e.clamp)return;let v=()=>i(p.scrollHeight>p.clientHeight+2),C=new ResizeObserver(v);return C.observe(p),()=>C.disconnect()},[e.clamp,n]);let c=e.clamp&&!r,u=`md${c?" clamped":""}`,m=c?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${u} ref=${t} style=${m}>
          ${(e.text??"").split(/\n{2,}/).map(p=>s`<p>${p}</p>`)}
        </div>`:s`<div class=${u} ref=${t} style=${m} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link small more" onClick=${()=>o(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function ge(e){let[t,n]=g(!!e.startEditing),[a,r]=g(e.value),[o,l]=g(null),[i,c]=g(null),u=O(null),m=O(!1);E(()=>l(null),[e.value]),E(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[p,v]=g(!1),C=e.locked??void 0,x=$=>{if(!$.target.closest("a, button, input, summary")){if(C)return v(!0);$.preventDefault(),r(o??e.value),c(null),m.current=!1,n(!0)}},_=()=>{m.current=!0,n(!1),c(null),e.onCancel?.()},f=async()=>{if(m.current)return;m.current=!0;let $=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if($===e.value.trim()||!$&&!e.multiline)return _();n(!1),l($);try{await e.onSave($)}catch(h){l(null),r($),c(h.message),m.current=!1,n(!0)}},w=$=>{if($.key==="Escape")return $.preventDefault(),$.stopPropagation(),_();$.key!=="Enter"||$.isComposing||$.keyCode===229||(!e.multiline||$.metaKey||$.ctrlKey)&&($.preventDefault(),f())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${$=>r($.target.value)} onKeyDown=${w} onBlur=${f}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let d=o??e.value;return s`<div class=${`editable${C?" locked":""}${o!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${C?`${e.label}: ${C}`:`Edit ${e.label}`}
      data-tip=${C} onClick=${x} onBlur=${()=>v(!1)}
      onKeyDown=${$=>$.key==="Enter"&&$.target===$.currentTarget&&x($)}>
    ${d.trim()?e.render?e.render(d):d:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${p&&C?s`<span class="edit-hint small locked-why" role="status"><${b} name="lock" size=${14} /> ${C}</span>`:null}
  </div>`}function bt(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${F(e.ci[0])}, ${F(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${F(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${F(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function yt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function An({node:e}){let t=Y("proposal"),n=Y("check"),a=t.data,r=n.data;if(!a)return s`<${te} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let o=a.proposal??{},l=(a.versions??[]).filter(c=>c.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${te} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${o.statement}</p>`}
    ${o.rationale?s`<p class="rationale prose">${o.rationale}</p>`:null}
    <div class="predictions">
      ${(r?.predictions??[]).map(c=>s`<div class="prediction" key=${c.name}>
          <${L} spec=${T("result",c.result)} />
          <span class="pname">${c.name}</span>
          <span class="pdetail num small">${bt(c)}</span>
        </div>`)}
    </div>
    ${l.length?s`<${mt} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>s`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function Hn({node:e}){let t=Y("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],r=a.find(i=>i.group===n)??null,o=a.filter(i=>i.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${Oe} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${s`<${L} spec=${{icon:"circle-help",tone:"muted",label:Ps}} />`}>
    <${ge} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${rt} text=${i} />`} onSave=${i=>vn(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=Rs)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${o.length?s`<p class="memory-meta small">Memory above this group: ${o.map((i,c)=>s`${c?", ":""}<a href=${S(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var Rs=5,Ps="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Os="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function Kn({node:e}){let t=Y("main"),n=e.data?.main.params.from??".",a=P(t.data).filter(r=>r.path!==n);return s`<${te} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${I}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(r=>{let[o,l]=yt(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${S(r.path)}
            onPointerEnter=${()=>Ae(r.path)} onFocus=${()=>Ae(r.path)}>
          <${L} spec=${T("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${T("research",r.status).tone}`}>${T("research",r.status).label}</span>`:null}
            ${r.check?s`<${L} spec=${T("result",r.check)} word />`:null}
            ${r.verdict?s`<${L} spec=${T("verdict",r.verdict)} />`:null}
            ${o?s`<span data-tip=${l}>${o}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${L} spec=${T("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${b} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Un({node:e}){let t=Y("main"),n=e.data?.main.params.from??".",[a,r]=g(!1),o=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),l=t.data?.meta?.matched??o.length;return s`<${Oe} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${L} spec=${{icon:"circle-help",tone:"muted",label:Os}} />
        ${s`<${W} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${Bs} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!o.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${o.map(i=>s`<${ot} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Fn} call=${e.data.main} before=${o[o.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Is=20;function Fn(e){let[t,n]=g(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Is}}:null,r=y(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let o=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${o.map(l=>s`<${ot} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${Fn} call=${e.call} before=${o[o.length-1]?.id} scope=${e.scope} />`:null}`}var zs=["observation","decision","idea","question","theory"];function jn(e){return(e?.note_types??zs).filter(t=>t!=="verdict")}function Bs(e){let t=jn(M(pe)),[n,a]=g("observation"),[r,o]=g(""),[l,i]=g(""),[c,u]=g(null),[m,p]=g(!1),v=async x=>{if(x.preventDefault(),!r.trim())return u("give the note a title");p(!0);try{await gn(e.group,n,r.trim(),l.trim()),e.onDone()}catch(_){u(_.message),p(!1)}};return s`<form class="note new-note" onSubmit=${v} onKeyDown=${x=>{x.key==="Escape"&&e.onDone(),x.key==="Enter"&&(x.metaKey||x.ctrlKey)&&v(x)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${x=>a(x.target.value)}>
        ${t.map(x=>s`<option value=${x}>${x}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${r} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${x=>o(x.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${l} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${x=>i(x.target.value)}></textarea></span>
    <div class="save-actions">
      <${ne} type="submit" icon=${m?"hourglass":"plus"} disabled=${m}>${m?"Adding\u2026":"Add note"}<//>
      <${ne} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${c?s`<span class="bad-text small">${c}</span>`:null}
    </div>
  </form>`}function As({note:e}){let t=jn(M(pe)).filter(n=>n!==e.type);return e.type==="verdict"?s`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${b} name=${T("note","verdict").icon} size=${15} /></span>`:s`<${We} icon=${T("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>s`<button type="button" key=${n} onClick=${()=>Je(e,{type:n})}>
        <${b} name=${T("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function ot(e){let t=e.note,[n,a]=g(!!e.open),[r,o]=g(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${b} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${As} note=${t} />
      <${ge} value=${t.description} label="the note's title" class="note-title heading" render=${Ks}
        onSave=${u=>Je(t,{description:u})} />
      ${t.overall?s`<${L} spec=${T("verdict",t.overall)} />`:null}
      ${t.state?s`<${Vt} tone="warn">${t.state}<//>`:null}
      ${l?s`<a class="note-group small" href=${S(l)} data-tip="from this group">${Hs(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${U(i)}</span>
      ${s`<${W} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${u=>{u.stopPropagation(),o(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ne} icon="trash" kind="danger" onClick=${()=>{yn(t)}}>Delete<//>
          <${ne} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${ge} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${u=>s`<${rt} text=${u} />`}
          onSave=${u=>Je(t,{body:u})} />`:null}
  </article>`}function Hs(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return le(a)?a.slice(-8):n}function Gn({node:e}){let t=Y("main"),n=t.data?.lines??[],a=t.data?.meta??{},r=s`<${b} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${te} result=${t}>
    <${mt} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Wn({node:e}){let t=ie(X);return s`<${te} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ge} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Te.value===e.id} onCancel=${()=>Te.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${rt} text=${n} />`}
      onSave=${n=>(Te.set(null),Ze(t.path,e.id,n))} />
  <//>`}function Vn({node:e}){return s`<${I} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Ks(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[r]=a.split(/[#@]/),o=r.split("/").pop()??"";return s`<a href=${le(o)?ce(o):S(r)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function qn(e){let t=()=>D(S(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${b} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${W} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${Us} id=${e.run} scope=${e.path} />`:s`<${Fs} path=${e.path} />`}
  </aside>`}function Us({id:e,scope:t}){let n=y(nt(e,t)).data,a=y(Dn(e,t)).data,r=y(Be(t)).data,o=y({method:"keys",params:{from:t},scope:t}).data,l=re(),i=Ne(()=>je(P(r).map(p=>p["run.id"]),l).get(e),[r,l,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let c=n.run,u=Object.entries(n.metrics??{}),m=Ht(i,l);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${m.class} style=${m.style}></span>
      <a href=${ce(e)}>${c.name}</a></h3>
    <p class="facts small">
      <${L} spec=${T("run",c.status)} word />
      <span><b>${ye(c.steps)}</b> steps</span>
      <span><b>${Ce(c.duration_s)}</b></span>
      <span data-tip=${c.created_at}>${U(c.created_at)}</span>
    </p>
    ${c.error?s`<pre class="log code bad-text">${c.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <${qe} config=${n.config??{}} varying=${ze(o)} />
    ${u.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${u.map(([p,v])=>s`<tr><td>${p}</td><td class="num"><b>${F(v.last)}</b></td>
              <td class="num">${F(v.min)}</td><td class="num">${F(v.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(p=>s`<p class="small"><${L} spec=${T("note",p.type)} /> ${p.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(p=>s`<div class="event small"><span class="muted num">${p.t?.slice(5,16).replace("T"," ")}</span>
        <${b} name=${$t(p.type)} size=${14} /><span>${p.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function Fs({path:e}){let t=y(st(e)).data,n=y(_n(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${ot} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${b} name=${a.kind==="note"?"file-text":$t(a.type)} size=${14} />
        <span>${a.run?s`<a href=${ce(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var wt=["failed","killed","lost"];function kt(e){let t=be(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=G(e.path)?[]:n.split("/"),r=a.length&&le(a[a.length-1])?a[a.length-1]:null,o=a.slice(0,-1),l=i=>[...t==="."?[]:[t],...o.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${o.map((i,c)=>s`<span>/</span><a href=${S(l(c))}>${i}</a>`)}
    </nav>
    ${r?s`<${Ws} id=${r} scope=${e.path} />`:s`<${js} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function js({path:e}){let t=P(y(tt(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=wt.reduce((r,o)=>r+(t[o]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${L} spec=${T("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${wt.filter(r=>t[r]).map(r=>`${t[r]} ${r}`).join(", ")}>
            <${b} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?wt.find(r=>t[r]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Yn} path=${e} />
    </p>`}function Xn({path:e}){let t=P(y(tt(e)).data)[0]??null,n=y(t?.proposal?Mn(e):null).data,a=y(t?.proposal?Nn(e):null).data;if(!t?.proposal)return null;let r=a?.proposal?.rationale,o=a?.versions?.find(c=>c.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,i]=yt(n?.progress?.text??t.progress);return s`<${z} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ge} value=${t.proposal} label="the proposal's statement" locked=${a?o:"Loading the proposal\u2026"}
          render=${c=>s`<span data-tip=${o?void 0:r}>${c}</span>`}
          onSave=${c=>bn(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let u=T("result",c.result),m=bt(c),p=m?`${u.label}: ${m}`:u.label;return s`<span class=${`check small tone-${u.tone}`} key=${c.name} data-tip=${p}
              aria-label=${`${c.name}: ${p}`} tabindex="0"><${b} name=${u.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${Gs} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Gs(e){let t=y(e.verdict?st(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=T("verdict",e.verdict),a=(t?.entries??[]).find(o=>o.type==="verdict"&&(o.group??e.path)===e.path),r=a?he(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${b} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${r}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${r?` \xB7 ${U(r)}`:""}</span>`:null}
  </p>`}function Ws({id:e,scope:t}){let n=y(nt(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,r=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${ge} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${o=>wn(a.id,t,o.trim())} />
      <${L} spec=${T("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${ye(a.steps)}</b> steps</span>
      <span><b>${Ce(a.duration_s)}</b></span>
      <span data-tip=${a.created_at}>${U(a.created_at)}</span>
      <${Yn} path=${t} />
      <${W} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${r} />
      <${We} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${Vs(a).map(([o,l])=>s`<tr><td class="muted">${o}</td><td>${l}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>D(S(t,{run:a.id}),{replace:!0})}>
            <${b} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${b} name="copy" size=${15} /> Copy the run id</button>
          ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
            <${b} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(o=>{let l=T("result",o.check);return s`<a class=${`check small tone-${l.tone}`} href=${S(o.group)} data-tip=${o.statement}>
              <${b} name=${l.icon} size=${14} />${o.group==="."?"own proposal":o.group}
              ${o.verdict?s`<${L} spec=${T("verdict",o.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Yn({path:e}){let t=y(vt(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([o,l])=>`${pt(o)} ${F(l)}`).join(", "),a=le(e.split("/").pop()??""),r=`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}${n?` (${n})`:""}`;return s`<span data-tip=${r}>
    best <b>${pt(`metric.${t.metric}.${t.stat}`)} ${F(t.value)}</b>
    ${a?null:s` · <a href=${ce(t.run)}>${t.name}</a>`}
  </span>`}function Vs(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var xt=80;function Jn({node:e}){let t=Y("main"),n=Y(e.data?.keys?"keys":""),a=e.props.mode==="run",r=e.props.title??(a?"Config":"Hyperparameters");return s`<${Oe} id=${`config:${e.id}`} title=${r} open=${e.props.open} result=${t}>
    ${t.data?a?s`<${qe} config=${t.data.config} varying=${ze(n.data)} />`:s`<${qs} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function qs({rows:e}){let t=new Set(ze({config:{rows:e}})),n=e.filter(([a])=>t.has(a.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([a,,r])=>{let o=Array.isArray(r)?r.map(F).join(", "):`${F(r.min)} \u2026 ${F(r.max)} \xB7 ${r.distinct} values`;return s`<tr><td data-tip=${a}>${a.replace(/^config\./,"")}</td>
      <td data-tip=${o.length>xt?o:void 0}>${o.length>xt?`${o.slice(0,xt-1)}\u2026`:o}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var Zn=15e3;function Qn({node:e}){let t=ie(X),n=re(),[a,r]=jt(),o=e.props.code,l=y(r&&o?{method:"code",params:o,scope:null}:null),[i,c]=g(null),[u,m]=g(120),[p,v]=g({error:null,warnings:[]}),C=w=>{de&&console.error(`[block ${e.id}] ${w}`),v(d=>({...d,error:w}))},x=O(()=>{});E(()=>{if(!i)return;let w=!0;De.n++;let d=()=>{w&&De.n--,w=!1};x.current=d;let $=setTimeout(()=>{w&&C(`no first render within ${Zn/1e3} s`),d()},Zn);return()=>{clearTimeout($),d()}},[i]),E(()=>{let w=i?.contentWindow;if(!w||l.status!=="ready")return;let d=N=>w.postMessage(N,"*"),$=new Map,h=new nn,H=N=>{if(N.source!==w)return;let k=N.data;switch(k.type){case"hello":d({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:Ft.value,pair:Ue.value,prefs:ft(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!Qt.has(k.call.method)){d({type:"result",id:k.id,result:{status:"error",data:null,error:`${k.call.method} is not available in a custom block`,refreshing:!1}});break}$.get(k.id)?.(),$.set(k.id,Lt(k.call,ae=>d({type:"result",id:k.id,result:ae})));break;case"unsub":$.get(k.id)?.(),$.delete(k.id);break;case"navigate":k.url.startsWith("/")&&D(k.url);break;case"height":h.accept(performance.now())?m(Math.max(40,k.height)):B("its height keeps changing, so it is fixed at its last height");break;case"ready":v(ae=>({...ae,blank:k.blank,overflow:k.overflow})),x.current();break;case"warn":B(k.message);break;case"hover":dt.set(k.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(k.prefs)&&A.set(k.prefs);break;case"download":case"snapshot":k.href?en(k.href,k.name)?performance.now()-j>1e3&&(j=performance.now(),Pe().download(k.href,k.name)):B(`a download of ${k.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":Pe().figure(k.spec,k.name).catch(ae=>B(`the PDF failed: ${ae.message}`));break;case"expand":tn(k.node)&&Pe().expand(k.node,t);break;case"error":C(k.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,_)),x.current();break;default:break}},B=N=>{de&&console.warn(`[block ${e.id}] ${N}`),v(k=>k.warnings.includes(N)?k:{...k,warnings:[...k.warnings,N]})},j=-1/0,A=ft(t.path),q=dt.subscribe(N=>d({type:"hover",run:N})),R=A.subscribe(N=>d({type:"prefs",prefs:N}));return addEventListener("message",H),d({type:"ping"}),()=>{q(),R(),removeEventListener("message",H);for(let N of $.values())N()}},[l.status,l.data?.code,i]),E(()=>{let w={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(w,"*")},[t.names,t.colors,t.metrics,i]),E(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let _=typeof o=="object"?o.path??o.block:String(o??"");Gt(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let f=r&&l.status==="ready"&&!p.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${f?s`<span class="chart-tools">
            <${W} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${W} icon="x" label="Close (Esc)" onClick=${()=>Re.set(null)} />`:s`<${W} icon="maximize" label="Expand" onClick=${()=>Pe().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${te} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${p.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${_})</span>
            <pre class="code">${p.error}</pre>
          </div>`:null}
      ${p.warnings.map(w=>s`<${I} kind="warning">${w}<//>`)}
      ${f?s`<div class="custom-frame" data-frame-blank=${p.blank?"1":void 0} data-frame-overflow=${p.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${Xs()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function Xs(){if(!!1)return{src:Dt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function es({node:e}){let t=Y("main"),n=ie(X),a=t.data?.entries??[];return s`<${te} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${I}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${_t(_e(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${Le?"eager":"lazy"} />
          <figcaption class="small">step ${ye(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function ts({node:e}){let t=Y("main"),n=t.data?.entries??[];return s`<${te} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${I}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${ye(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function ns({node:e}){let[t,n]=g(Le||e.props.open!==!1),a=s`${(e.children??[]).map(l=>s`<${se} key=${l.id} node=${l} />`)}`,r=ie(Ge);if(!e.props.title)return s`<div class="stack">${a}</div>`;let o=r===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${t} aria-label=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${()=>n(!t)}>
      <${b} name=${t?"chevron-down":"chevron-right"} size=${16} />${o?null:e.props.title}
    </button>
    ${t?s`<div class="stack">${a}</div>`:null}
  </div>`}function ss({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${se} key=${n.id} node=${n} />`)}
  </div>`}function as({node:e}){let t=ie(X),n=Xe(t.path),a=e.props.min_width??320,r=e.props.columns,o=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${a}px, 100%), 1fr))`,l=(e.children??[]).flatMap(m=>m.props.y??[]),i=e.props.addable?n.added.filter(m=>!l.includes(m)).map(m=>({block:"line",id:`added-${m}`,props:{y:m,added:!0},data:{main:{...e.props.template,params:{...e.props.template.params,y:[m]}}}})):[],c=Zt([...e.children??[],...i],n.order[e.id]),u=(m,p)=>{let v=c.map(C=>C.id).filter(C=>C!==m);v.splice(v.indexOf(p),0,m),Yt(t.path,e.id,v)};return s`<div class="grid" style=${o}>
    ${c.map(m=>s`<${Ys} key=${m.id} node=${m} path=${t.path} span=${n.spans[m.id]??m.props.span??1}
      columns=${r} onDrop=${p=>p!==m.id&&u(p,m.id)} />`)}
    ${e.props.addable&&!!1?s`<${Js} path=${t.path} shown=${[...l,...n.added]} />`:null}
  </div>`}var St=[1,2,"full"];function Ys(e){let[t,n]=g(!1),a=St[(St.indexOf(e.span)+1)%St.length],r=o=>o==="full"?"full width":`${o} column${o===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${o=>{o.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${o=>{o.preventDefault(),n(!1),e.onDrop(o.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${o=>o.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${b} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(a)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>Jt(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${se} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Js(e){let t=y({method:"keys",params:{from:e.path},scope:e.path}).data,n=(t?.metrics?.rows??[]).map(a=>a[0]).filter(a=>!e.shown.includes(a));return t&&!n.length?null:s`<div class="add-chart">
    <span class="add-chart-label"><${b} name="plus" size=${16} /> Add a chart</span>
    <${Ve} single options=${n} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([a])=>Ye(e.path,r=>({added:[...r.added,a]}))} />
  </div>`}function rs({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,r]=g(()=>t.find(i=>i.id===n())?.id??t[0]?.id),o=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},l=t.find(i=>i.id===a)??t[0];return Le?s`<div class="stack">${t.map(i=>s`<${se} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===l?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>o(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(i=>s`<${se} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var Zs={section:ns,row:ss,grid:as,line:dn,table:fn,stat:$n,images:es,text:ts,proposal:An,note:Vn,output:Gn,config:Jn,memory:Hn,groups:Kn,notes:Un,tabs:rs,scatter:un,bar:mn,histogram:pn,data_table:rn,timeline:on,custom:Qn,markdown:Wn};function se({node:e}){return s`<${qt} node=${e} blocks=${Zs} />`}function os(e,t){let n=e.split(`
`),a=t.split(`
`),r=n.length,o=a.length,l=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let m=r-1;m>=0;m--)for(let p=o-1;p>=0;p--)l[m][p]=n[m]===a[p]?l[m+1][p+1]+1:Math.max(l[m+1][p],l[m][p+1]);let i=[],c=0,u=0;for(;c<r&&u<o;)n[c]===a[u]?(i.push({kind:"same",text:n[c]}),c++,u++):l[c+1][u]>=l[c][u+1]?i.push({kind:"removed",text:n[c++]}):i.push({kind:"added",text:a[u++]});for(;c<r;)i.push({kind:"removed",text:n[c++]});for(;u<o;)i.push({kind:"added",text:a[u++]});return i}function is(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let r=a;for(;r<e.length&&e[r].kind==="same";)r++;let o=a===0?0:t,l=r===e.length?0:t;r-a>o+l+1?n.push(...e.slice(a,a+o),{kind:"skip",count:r-a-o-l},...e.slice(r-l,r)):n.push(...e.slice(a,r)),a=r}return n}var Ct={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function ls(e){if(Ct[e.block])return Ct[e.block];if(e.block==="row"||e.block==="grid"){if(e.props.addable)return"charts";let n=new Set((e.children??[]).map(r=>Ct[r.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function it(e){let t=y(Be(e.path)),n=re(),a=P(t.data),r=Ne(()=>je(a.map(m=>m["run.id"]),n),[t.data,n]),o=Ne(()=>new Map(a.map(m=>[m["run.id"],m["run.name"]??m["run.id"]])),[t.data]),l=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${l}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${z} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let i={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}},c=e.view.view;if(e.plain)return s`<div class=${l}><${X.Provider} value=${i}><${se} node=${c} /><//></div>`;let u=c.block==="section"&&!c.props.title?c.children??[]:[c];return s`<div class=${l}>${e.before}
    <${X.Provider} value=${i}>
      ${u.map(m=>{let p=ls(m);return s`<${z} key=${m.id} label=${p}><${Ge.Provider} value=${p}><${se} node=${m} /><//><//>`})}
    <//>
  </div>`}function cs(e){if(null)return s`<div class="view-source small"><${b} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=M(V),a=n.page==="group"&&n.version,r=t.versions?s`<a href=${S(e.path,{history:!0})}><${b} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=s`draft <b>${t.draft}</b>`;break;case"view":o=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${U(he(t.version))} by ${t.author??"unknown"}`;break;default:o=s`the built-in view`}return s`<div class="view-source small">
    <${b} name="layout" size=${14} /><span>${o}</span>
    ${a?s`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!a?s`<${Qs} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${ea} path=${e.path} />
        <${ta} path=${e.path} view=${t} />`}
  </div>`}function Qs(e){let[t,n]=g(null),a=e.outdated.map(o=>o.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await kn(e.path)}catch(o){n(o.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${b} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function ea(e){let[t,n]=g(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Te.set(await Ze(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${b} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function ta(e){let t=Xe(e.path),n=Xt(t),[a,r]=g(!1),[o,l]=g(e.view.title??""),[i,c]=g(e.view.finding??""),[u,m]=g(null),[p,v]=g(!1);if(!n&&!a)return null;let C=async x=>{x.preventDefault(),v(!0),m(null);try{let _={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await K("save_view",{path:e.path,prefs:_,title:o,finding:i}),Ye(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),Se(f=>["view","view_history","summary"].includes(f.method)&&f.scope===e.path),r(!1)}catch(_){m(_.message)}finally{v(!1)}};return a?s`<form class="save-form" onSubmit=${C}>
    <${Ie} label="Title"><input value=${o} onInput=${x=>l(x.target.value)} /><//>
    <${Ie} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${x=>c(x.target.value)} /><//>
    <div class="save-actions">
      <${ne} type="submit" icon=${p?"hourglass":"save"} disabled=${p}>${p?"Saving\u2026":"Save as view"}<//>
      <${ne} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${u?s`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:s`<${ne} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function ds(e){let t=y(Pn(e.path)),n=t.data?.entries??[],[a,r]=g(null),o=a??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let c=o.includes(i)?o.filter(u=>u!==i):[...o,i].slice(-2);r(c.sort())};return t.status==="error"?s`<${I} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${b} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${I}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,c)=>s`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${U(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${c===0?S(e.path):S(e.path,{version:i.version})}
            onClick=${u=>{u.preventDefault(),D(c===0?S(e.path):S(e.path,{version:i.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?s`<${na} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function na(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=y(t(e.a)).data,a=y(t(e.b)).data,r=y($e(e.path,e.a)).data,o=y($e(e.path,e.b)).data,l=n&&a?is(os(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${U(he(e.a))} to ${U(he(e.b))}</h3>
    <pre class="diff code">${l.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${it} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${o?.title??e.b}</h3><${it} path=${e.path} view=${o} plain /></div>
    </div>
  </div>`}function us(e){return E(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?s`<div class="page"><div class="sections">
      <${z} label=${ms(e.path)}><${kt} path=${e.path} /><//>
      <${z} label="history"><${ds} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${sa} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function sa(e){let t=y($e(e.path,e.version,e.draft));E(()=>{t.status==="ready"&&requestAnimationFrame(zt)},[t.status==="ready"]);let n=s`
    <${z} label=${ms(e.path)}>
      <${kt} path=${e.path} finding=${t.data?.finding} />
      ${t.data?s`<${cs} path=${e.path} view=${t.data} />`:null}
    <//>
    ${le(e.path.split("/").pop()??"")?null:s`<${Xn} path=${e.path} />`}`;return t.status==="error"?s`<div class="sections">${n}
      <${z} label="view">
        ${aa(e.path,t.error)?s`<${I} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${I} kind="error">${t.error}<//>`}
      <//>
    </div>`:s`<${it} path=${e.path} view=${t.data} before=${n} />`}function ms(e){return le(e.split("/").pop()??"")?"run":"group"}function aa(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function ps(e){E(()=>{xe($e(e.id)).then(n=>D(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=y($e(e.id));return t.status==="error"?s`<div class="page"><${I} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var ra={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Et=20,Me=-1,oa=[["day",86400],["week",7*86400],["month",30*86400]];function fs(e){let t=P(y(oe()).data).map(i=>i.path),n=y({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=y({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});E(()=>{document.title="Timeline \xB7 Beamtime"},[]);let r=Date.now()/1e3,o=P(n.data).filter(i=>i["run.created_at"]).map((i,c)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:c})),l=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(he(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${z} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Ie} label="Group" inline>
          <select value=${e.from} onChange=${i=>D(Ke(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${o.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${z} label="runs">
      ${n.status==="error"?s`<${I} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${ia} bars=${o} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function ia(e){let t=re(),n=O(null),a=[...e.bars.flatMap(f=>[f.start,f.end]),...e.marks.map(f=>f.t)],r=a.length?$s(Math.min(...a),Math.max(...a)):$s(Date.now()/1e3-86400,Date.now()/1e3),[o,l]=g(r),i=e.bars.length,c=Math.min(900,Math.max(160,(i+1.5)*Et+40)),m=ln(n,cn,t?(f=>{let w=sn(o[0],o[1]),d=h=>f.colors[ra[h]??"muted"],$=h=>f.colors[h==="verdict"?"good":h==="decision"?"accent":h==="question"?"warn":"muted"];return{style:Ut(f),height:c,x:{range:o,log:!1,format:h=>an(h,w.step),splits:w.at},y:{range:[Me-.8,i+.5],log:!1,reverse:!0,size:150,splits:i<=40?[Me,...e.bars.map(h=>h.lane)]:[Me],format:h=>h===Me?"notes":ma(e.bars[Math.round(h)]?.name??"")},draw:({ctx:h,x:H,y:B,px:j,focused:A})=>{let q=Et*.62*j;for(let R of e.bars){let N=H(R.start),k=Math.max(3*j,H(R.end)-N);h.fillStyle=A!==null&&A!==R.id?Kt(d(R.status),.35):d(R.status),h.beginPath(),h.roundRect(N,B(R.lane)-q/2,k,q,3*j),h.fill()}for(let R of e.marks){let N=H(R.t),k=B(Me),ae=(A===R.id?6:4.5)*j;h.fillStyle=$(R.type),h.beginPath(),h.moveTo(N,k-ae),h.lineTo(N+ae,k),h.lineTo(N,k+ae),h.lineTo(N-ae,k),h.closePath(),h.fill()}},hit:(h,H,B,j)=>{if(Math.abs(H-j(Me))<Et/2){let R=ua(e.marks,N=>Math.abs(B(N.t)-h),8);return R?{key:R.id,rows:ca(R)}:null}let A=Math.round((H-j(0))/(j(1)-j(0))),q=e.bars.find(R=>R.lane===A&&B(R.start)-3<=h&&h<=Math.max(B(R.end),B(R.start)+3)+3);return q?{key:q.id,rows:la(q)}:null},onClick:h=>{let H=e.marks.find(B=>B.id===h);H?D(S(H.group,{drawer:!0})):D(ce(h))}}})(t):null,[o,e.bars,e.marks],t),p=f=>{if(!m.current)return;f.preventDefault();let w=m.current.xAt(f.clientX),d=Math.exp(f.deltaY*.0015);l(([$,h])=>Tt([w-(w-$)*d,w+(h-w)*d],r))},v=O(null),C=f=>v.current={x:f.clientX,range:o},x=f=>{if(!v.current||!m.current||!(f.buttons&1))return;let w=(f.clientX-v.current.x)*m.current.xPerPixel(),[d,$]=v.current.range;Math.abs(f.clientX-v.current.x)>3&&l(Tt([d-w,$-w],r))},_=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${oa.map(([f,w])=>s`<button type="button" role="radio" aria-checked=${Math.abs(o[1]-o[0]-w)<1}
          onClick=${()=>l(Tt([_-w,_+w*.02],[Math.min(r[0],_-w),r[1]]))}>last ${f}</button>`)}
      <button type="button" role="radio" aria-checked=${o[0]===r[0]&&o[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${p} onPointerDown=${C} onPointerMove=${x} onPointerUp=${()=>v.current=null}></div>
    <p class="muted small">${da(t)}</p>
  </div>`}function la(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:U(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Ce(e.end-e.start),color:null}]}function ca(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:U(new Date(e.t*1e3).toISOString()),color:null}]}function da(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function ua(e,t,n){let a=null,r=n;for(let o of e){let l=t(o);l<r&&([a,r]=[o,l])}return a}function $s(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Tt([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-a));return[r,r+a]}function ma(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function hs(){let e=M(Re),t=O(null);if(E(()=>{let r=t.current;if(!r||!e)return;r.showModal();let o=()=>Re.set(null);return r.addEventListener("close",o),()=>r.removeEventListener("close",o)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${X.Provider} value=${e.view}><${se} node=${n} /><//>
  </dialog>`}function gs(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let r=a.indexOf(n);if(r>=0)return 100-Math.min(r,50)-a.length/100;let o=0,l=0;for(let i of a)if(i===n[o]?o++:o>0&&l++,o===n.length)return 40-Math.min(l,39);return 0}function bs(e){let[t,n]=g(e.query),[a,r]=g(0),o=O(null),l=P(y(oe()).data),i=P(y(at()).data);E(()=>{let d=o.current;d.showModal();let $=()=>Z.set(null);d.addEventListener("close",$);let h=!1,H=A=>{let q=d.getBoundingClientRect();return A.clientX<q.left||A.clientX>q.right||A.clientY<q.top||A.clientY>q.bottom},B=A=>h=H(A),j=A=>h&&H(A)&&d.close();return"closedBy"in HTMLDialogElement.prototype||(d.addEventListener("pointerdown",B),d.addEventListener("pointerup",j)),()=>{d.removeEventListener("close",$),d.removeEventListener("pointerdown",B),d.removeEventListener("pointerup",j)}},[]);let c=()=>o.current?.close(),u=d=>()=>D(d),m=V.value,p=m.page==="group"?m.path:".",v=(d,$,h,H)=>({section:"Commands",label:d,detail:$,sym:{icon:h,tone:"muted",label:d},run:H}),x=[...l.map(d=>({section:"Groups",label:d.path==="."?"local":d.path,detail:`${d.runs} runs${d.proposal?` \xB7 ${d.proposal}`:""}`,sym:T("research",d.status),run:u(S(d.path))})),...i.map(d=>({section:"Runs",label:d["run.name"]??d["run.id"],detail:`${d["run.status"]} \xB7 ${d["run.path"]}`,sym:T("run",d["run.status"]),run:u(S(d["run.path"]))})),v("Theme: light","","sun",()=>Fe("light")),v("Theme: dark","","moon",()=>Fe("dark")),v("Theme: follow the system","","monitor",()=>Fe("system")),v("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),v("Show notes and timeline","i","file-text",u(S(p,{drawer:!0}))),v("Show or hide the sidebar","\u2318B","panel-left",()=>J.set(!J.value)),v(ee.value?"Resume live updates":"Pause live updates","p",ee.value?"play":"pause",()=>ee.set(!ee.value)),v("Keyboard shortcuts","?","keyboard",()=>me.set(!0)),v("Settings","","settings",u("/settings/appearance"))].map(d=>({it:d,s:Math.max(gs(t,d.label),gs(t,d.detail)*.5)})).filter(d=>d.s>0).sort((d,$)=>$.s-d.s||vs(d.it.section)-vs($.it.section)).slice(0,60).map(d=>d.it),_=d=>{d&&(c(),d.run())},f=d=>{if(d.key==="ArrowDown")r(Math.min(x.length-1,a+1));else if(d.key==="ArrowUp")r(Math.max(0,a-1));else if(d.key==="Enter")_(x[a]);else return;d.preventDefault()},w="";return s`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${b} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${x[a]?`pal-${a}`:void 0}
        onInput=${d=>{n(d.target.value),r(0)}} onKeyDown=${f} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${x.map((d,$)=>{let h=d.section!==w&&!t?w=d.section:null;return s`${h?s`<li class="palette-head small" role="presentation">${h}</li>`:null}
          <li id=${`pal-${$}`} class="item" role="option" aria-selected=${$===a}
              onMouseMove=${()=>r($)} onClick=${()=>_(d)}>
            <${L} spec=${d.sym} /><span class="label">${d.label}</span><span class="detail small">${d.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function vs(e){return["Groups","Runs","Commands"].indexOf(e)}function lt(e,t=[]){let n=new Map,a=(o,l={})=>({path:o,name:o==="."?"local":o.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let o of e)n.set(o.path,a(o.path,o));n.has(".")||n.set(".",a("."));for(let o of t)o.name!=="local"&&(n.has(o.name)||n.set(o.name,a(o.name)),Object.assign(n.get(o.name),{state:o.state,error:o.error}));for(let o of n.values()){if(G(o.path))continue;let l=o.path.lastIndexOf("/"),i=l<0?".":o.path.slice(0,l);(n.get(i)??n.get(be(o.path))??n.get(".")).children.push(o)}for(let o of n.values())o.children.sort((l,i)=>l.name.localeCompare(i.name));let r=[...n.values()].filter(o=>o.path!=="."&&G(o.path)).sort((o,l)=>o.name.localeCompare(l.name));return[n.get("."),...r]}function ys(e,t,n,a=new Set){let r=[],o=n.toLowerCase(),l=i=>{(!o||i.path.toLowerCase().includes(o)||ws(i,o))&&(r.push(i),(o||(G(i.path)?!a.has(i.path):t.has(i.path)))&&i.children.forEach(l))};return e.forEach(l),r}function ws(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||ws(n,t))}function ks(e,t){if(G(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),r=o=>o.path===a?o:o.children.map(r).find(l=>l)??null;return e.map(r).find(o=>o)?.children??[]}function xs(e){return G(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Ss(){let e=M(V),t=y(oe()),[n,a]=g(()=>new Set(we("open",[]))),[r,o]=g(()=>new Set(we("closed-hosts",[]))),[l,i]=g(""),c=O(null),u=e.page==="group"?e.path:null,m=lt(P(t.data),t.data?.meta?.sources??[]),p=ys(m,fa(n,u),l,r),v=f=>G(f)?!r.has(f):n.has(f),C=(f,w)=>{let d=w??!v(f);if(G(f)){let h=new Set(r);d?h.delete(f):h.add(f),ke("closed-hosts",[...h]),o(h);return}let $=new Set(n);d?$.add(f):$.delete(f),ke("open",[...$]),a($)},x=O(u);return E(()=>{u!==x.current&&u&&!G(u)&&r.has(be(u))&&C(be(u),!0),x.current=u},[u]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${b} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${l} aria-label="Filter groups"
        onInput=${f=>i(f.target.value)} />
    </label>
    <div class="tree" ref=${c} onKeyDown=${f=>{let w=[...c.current?.querySelectorAll("a.tree-item")??[]],d=w.indexOf(document.activeElement),$=p[d];switch(f.key){case"ArrowDown":w[Math.min(w.length-1,d+1)]?.focus();break;case"ArrowUp":w[Math.max(0,d-1)]?.focus();break;case"ArrowRight":$?.children.length&&C($.path,!0);break;case"ArrowLeft":$?.children.length&&v($.path)?C($.path,!1):$&&w[p.findIndex(h=>h.path===$a($.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${p.map(f=>s`<${pa} key=${f.path} node=${f} current=${f.path===u}
        open=${v(f.path)||!!l} onToggle=${()=>C(f.path)} />`)}
    </div>
  </nav>`}function pa(e){let t=e.node,n=()=>Ae(t.path),a=t.children.length>0,r=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&G(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${8+xs(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${o=>{o.metaKey||o.ctrlKey||(o.preventDefault(),D(S(t.path)))}}>
    <span class="twisty" onClick=${o=>{o.preventDefault(),o.stopPropagation(),e.onToggle()}}>
      ${a?s`<${b} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${G(t.path)?s`<${L} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${L} spec=${T("run","running")} size=${14} />`:null}
      ${t.failed?s`<${L} spec=${{...T("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function $a(e){if(G(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function fa(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let r=1;r<a.length;r++)n.add(a.slice(0,r).join("/"));return n}function Es(){let e=M(V),t=M(J),n=M(Z),a=M(me),r=O(null);E(()=>It(()=>r.current),[]),E(()=>(addEventListener("keydown",Cs),()=>removeEventListener("keydown",Cs)),[]);let o=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${us} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=s`<${ps} id=${e.id} />`;break;case"settings":l=s`<${Tn} />`;break;case"timeline":l=s`<${fs} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return de||!1?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${In} />
    ${t?s`<${Ss} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${o?s`<${qn} path=${e.path} run=${e.run} />`:null}
    <${zn} />
    ${n!==null?s`<${bs} query=${n} />`:null}
    ${a?s`<${ga} />`:null}
    <${hs} />
  </div>`}function Cs(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),Z.set(Z.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),J.set(!J.value);return}if(e.key==="Escape"){if(Z.value!==null||me.value)return;let a=V.value;return a.page==="group"&&a.run?D(S(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?D(S(a.path),{replace:!0}):void 0}if(t||e.altKey||Cn(e)||Z.value!==null||me.value)return;let n=V.value;switch(e.key){case"/":e.preventDefault(),Z.set("");break;case"?":me.set(!me.value);break;case"p":ee.set(!ee.value);break;case"i":n.page==="group"&&D(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":J.set(!J.value);break;case"[":case"]":n.page==="group"&&ha(n.path,e.key==="]"?1:-1);break}}async function ha(e,t){let n=await xe(oe()),a=ks(lt(P(n),n?.meta?.sources??[]),e),r=a.findIndex(l=>l.path===e),o=a[r+t];o&&D(S(o.path))}function ga(){let e=O(null);return E(()=>{let t=e.current;t.showModal();let n=()=>me.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${Qe.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ne} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Bt();if(de){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ue.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>De.n,At&&Wt()}hn();var va=K("meta").then(e=>(de&&(e={...e,settings:{...e.settings,theme_mode:ue.value}}),et(e),e));!de&&!!1&&Ot(async()=>{let[e,t]=await Promise.all([va,K("meta")]);e.bundle!==t.bundle?location.reload():et(t)});Mt(s`<${Es} />`,document.getElementById("app"));
