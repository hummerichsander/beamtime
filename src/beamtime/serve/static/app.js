import{$ as He,A as Qt,Aa as rt,B as me,Ba as St,C as ze,D as en,Da as gn,E as Je,F as wt,G as pe,Ga as vn,H as on,I as kt,J as Ze,Ja as bn,K as U,Ka as yn,L as J,La as wn,M as de,Ma as Cn,N as Qe,Na as Sn,O as rn,Oa as En,Q as Me,Qa as Tn,R as Ne,Sa as Mn,T as an,Ta as Nn,U as ln,Ua as Dn,V as k,Va as Pn,W as I,Wa as Rn,X as et,Xa as Ln,Y as re,Ya as _n,Z as z,_ as P,a as s,aa as F,ba as Ae,ca as O,d as K,da as ae,e as Oe,ea as Ke,f as Se,fa as Ue,g as yt,ga as tt,h as w,ha as nt,i as Vt,ia as cn,j as ne,ja as Fe,k as qt,ka as te,l as Xt,la as st,m as Yt,n as Ee,o as se,oa as dn,p as S,pa as un,q as Ye,qa as We,r as oe,ra as mn,s as Te,sa as pn,t as ke,ta as $n,u as G,ua as N,v as V,va as ot,w as Jt,wa as Ct,xa as fn,y as R,ya as hn,z as Zt,za as je}from"./chunks/chunk-SBH4MYIQ.js";import{a as jt,b as Gt}from"./chunks/chunk-O2K4N3UR.js";import{B as nn,C as sn,D as ie,G as be,H as xe,I as Ce,J as W,K as xt,V as kn,W as xn,b as Ut,d as Ft,f as y,g as T,h as Wt,i as L,j as Ie,k as Y,n as we,o as M,p as ge,q as ve,v as tn,x as Be}from"./chunks/chunk-2WY2FYB7.js";import"./chunks/chunk-VC46IEJQ.js";function De(e,t){Ee(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var Et=["notes","timeline","groups","check","card","memory_show","status"];async function at(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),De(e.group,Et)}async function In(e,t,n,o){await K("note_add",{group:e,type:t,description:n,body:o}),De(e,Et)}async function On(e,t){await K("memory_update",{group:e,body:t}),De(e,["memory_show","status"])}async function zn(e,t){let n=await K("proposal_show",{group:e}),o=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await K("proposal_set",{group:e,proposal:{...o,statement:t}}),De(e,["groups","proposal_show","check","summary"])}async function Bn(e){await K("note_rm",{note:e.id}),De(e.group,Et)}async function Hn(e,t,n){await K("name",{run:e,name:n}),De(t,["card","runs","groups","summary","series"])}async function it(e,t,n){let o=await K("view_text",{path:e,id:t,text:n});return Ee(r=>["view","view_history"].includes(r.method)&&r.scope===e),o.id}async function An(e){await K("view_upgrade",{group:e}),Ee(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Pe=new we(null);async function Kn(e,t){return await K("set",{key:e,value:t}),K("meta")}var ue=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),$e=(e,t=null,n=null,o=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...o?{metrics:o}:{}},scope:e}),Tt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),Re=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Un=e=>({method:"check",params:{group:e},scope:e}),Fn=e=>({method:"proposal_show",params:{group:e},scope:e}),Le=(e,t)=>({method:"card",params:{run:Te(e,t)},scope:t}),Wn=(e,t)=>({method:"output",params:{run:Te(e,t),tail:30},scope:t}),jn=(e,t)=>({method:"run_diff",params:{run:Te(e,t)},scope:t}),Ge=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),lt=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Gn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Vn=()=>({method:"status",params:{},scope:"."}),ct=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ve(e){let t=Fe(e).value.main;for(let n of[$e(e,null,null,t),Re(e),Ge(e),Tt(e,t)])yt(n);Se($e(e,null,null,t)).then(n=>{for(let o of qn(n.view))yt(o)}).catch(()=>{})}function qn(e){return e?[...qs.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(qn)]:[]}var qs=new Set(["line","custom"]),Xn=e=>({method:"view_history",params:{group:e},scope:e});var Mt="/static/favicon.svg",dt=null;async function Xs(){if(dt)return dt;let e=new Image;e.src=Mt,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let o=n.getContext("2d");if(!o)return Mt;o.drawImage(e,0,0,t,t),o.beginPath(),o.arc(t-6,t-6,6,0,Math.PI*2);let r=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return o.fillStyle=r||"#2f5aa8",o.fill(),dt=n.toDataURL("image/png"),dt}function Ys(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=Mt;return}Xs().then(n=>{t.type="image/png",t.href=n})}}function qe(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,Ys(t>0)},[e,t])}function Yn(e){let t=se(e.split("/").pop()??""),n=w(t?null:Re(e)),o=w(t?Le(e.split("/").pop()??"",e):null),r=t?o.data?.run.name??o.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,a=t?o.data?.run.status==="running"?1:0:P(n.data)[0]?.running??0;qe(r,a)}var Z=new we(ge("sidebar",!0)),Q=new we(null),fe=new we(!1),he=new we(null);Z.subscribe(e=>ve("sidebar",e));var Jn=ge("visit",Date.now());ve("visit",Date.now());function Zn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var ut=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Js=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function mt(e){he.set(e),Je.set(e.theme),Be.set(e.colormaps),e.settings?.theme_mode&&pe.set(e.settings.theme_mode),kt()}var Qn=0;async function Nt(e,t){let n=++Qn;e==="theme_mode"&&(pe.set(t),kt());let o=await Kn(e,t);n===Qn&&mt(o)}function es(){let e=M(pe),t=de(),n=M(he),[o,r]=y(null);qe("Settings");let a=(l,d)=>{r(null),Nt(l,d).catch(v=>r(v.message))},c=n?.settings??{},i=(l,d,v)=>s`
    <label class="field-label small" for=${`setting-${l}`}>${d}</label>
    <span class="input body">
      <select id=${`setting-${l}`} value=${c[l]} onChange=${m=>a(l,m.target.value)}>
        ${v.map(m=>s`<option value=${m}>${m}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${O} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${c.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${o?s`<${z} kind="error">${o}<//>`:null}
    <//>
    <${O} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Js.map(([l,d,v])=>s`<button type="button" role="radio" aria-checked=${e===l} onClick=${()=>a("theme_mode",l)}>
            <${k} name=${d} size=${15} />${v}</button>`)}
        </div>
        ${i("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(l=>s`<${z} kind="warning">${l}<//>`)}
    <//>
    <${O} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${nt} options=${n.figure_styles} value=${c.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${l=>a("figure_style",l)} />`:s`<span class="muted small"><code>${JSON.stringify(c.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(c.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${O} label="keyboard">
      <table class="kv">${ut.map(([l,d])=>s`<tr><td><kbd class="small">${l}</kbd></td><td>${d}</td></tr>`)}</table>
    <//>
    <${O} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(l=>s`
          <tr><td class="muted">${l.name}</td><td><code class="code">${l.logdir}</code> (${l.kind}, ${l.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var ts={system:"light",light:"dark",dark:"system"},Zs={system:"monitor",light:"sun",dark:"moon"};function ns(){let e=M(he),t=M(pe),n=M(Z);return s`<header class="topbar">
    <${F} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Z.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>Q.set("")} aria-label="Search (⌘K)">
      <${k} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Qs} />
      <${F} icon=${Zs[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${ts[t]})`}
        onClick=${()=>{Nt("theme_mode",ts[t])}} />
      <a class="icon-button" href=${Ye(V.value.page==="group"?V.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${k} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${k} name="settings" size=${16} /></a>
    </div>
  </header>`}function Qs(){let t=(w(ue()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${S(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${k} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${k} name="server" size=${15} /> local</span>`}function eo(e){let[t,n]=y(Date.now());return T(()=>{let o=setInterval(()=>n(Date.now()),e);return()=>clearInterval(o)},[e]),t}function to(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function ss(){let e=M(qt),t=M(ne),n=M(Xt),o=M(V),r=eo(5e3),a=w(Vn()).data,c=P(w(ct()).data),i=M(he),l=a?.daemon,d=a?.runs?.running??0,v=c.filter(E=>E["run.status"]==="failed"&&to(E["run.ended_at"])>Jn).length,m=a?.meta?.freshness,[p,$,g]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&l?["",`live \xB7 updated ${W(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${l.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${g}><span class=${`live-dot ${p}`}></span>${$}</span>
    ${d?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>Q.set("running")}>
          <${k} name="circle-dot" size=${14} class="tone-accent" />${d} running</button>`:null}
    ${v?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>Q.set("failed")}>
          <${k} name="circle-x" size=${14} />${v} failed since your last visit</button>`:null}
    ${m?.behind?s`<span class="status-item warn-text" data-tip=${m.text}><${k} name="hourglass" size=${14} />${m.behind} runs behind</span>`:null}
    ${m?.damaged?.length?s`<span class="status-item warn-text" data-tip=${m.damaged.join(`
`)}><${k} name="triangle-alert" size=${14} />${m.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${o.page==="group"&&o.run?s`<span class="status-item"><${k} name="activity" size=${14} />1 run selected</span>`:null}
    <${F} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ne.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var os=null;function pt(e){let t=L(null),[n,o]=y(null),[r,a]=y(!1),[c,i]=y(!1);T(()=>{let m=!0;return os??=import("./chunks/md-SW3VT2BQ.js"),os.then(p=>p.render(e.text??"")).then(p=>m&&o(p)),()=>{m=!1}},[e.text]),Wt(()=>{let m=t.current;if(!m||!e.clamp)return;let p=()=>i(m.scrollHeight>m.clientHeight+2),$=new ResizeObserver(p);return $.observe(m),()=>$.disconnect()},[e.clamp,n]);let l=e.clamp&&!r,d=`md${l?" clamped":""}`,v=l?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${d} ref=${t} style=${v}>
          ${(e.text??"").split(/\n{2,}/).map(m=>s`<p>${m}</p>`)}
        </div>`:s`<div class=${d} ref=${t} style=${v} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(c||r)?s`<button type="button" class="link small more" onClick=${()=>a(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function ye(e){let[t,n]=y(!!e.startEditing),[o,r]=y(e.value),[a,c]=y(null),[i,l]=y(null),d=L(null),v=L(!1);T(()=>c(null),[e.value]),T(()=>{!t||!d.current||(d.current.focus(),e.startEditing?d.current.select():d.current.setSelectionRange(d.current.value.length,d.current.value.length))},[t]);let[m,p]=y(!1),$=e.locked??void 0,g=f=>{if(!f.target.closest("a, button, input, summary")){if($)return p(!0);f.preventDefault(),r(a??e.value),l(null),v.current=!1,n(!0)}},E=()=>{v.current=!0,n(!1),l(null),e.onCancel?.()},h=async()=>{if(v.current)return;v.current=!0;let f=e.multiline?o.trim():o.replace(/\s*\n\s*/g," ").trim();if(f===e.value.trim()||!f&&!e.multiline)return E();n(!1),c(f);try{await e.onSave(f)}catch(b){c(null),r(f),l(b.message),v.current=!1,n(!0)}},x=f=>{if(f.key==="Escape")return f.preventDefault(),f.stopPropagation(),E();f.key!=="Enter"||f.isComposing||f.keyCode===229||(!e.multiline||f.metaKey||f.ctrlKey)&&(f.preventDefault(),h())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${d} class="edit-field" value=${o} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,o.split(`
`).length+1)):1}
        onInput=${f=>r(f.target.value)} onKeyDown=${x} onBlur=${h}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let u=a??e.value;return s`<div class=${`editable${$?" locked":""}${a!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${$?`${e.label}: ${$}`:`Edit ${e.label}`}
      data-tip=${$} onClick=${g} onBlur=${()=>p(!1)}
      onKeyDown=${f=>f.key==="Enter"&&f.target===f.currentTarget&&g(f)}>
    ${u.trim()?e.render?e.render(u):u:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${m&&$?s`<span class="edit-hint small locked-why" role="status"><${k} name="lock" size=${14} /> ${$}</span>`:null}
  </div>`}function Dt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function rs({node:e}){let t=J("proposal"),n=J("check"),o=t.data,r=n.data;if(!o)return s`<${re} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let a=o.proposal??{},c=(o.versions??[]).filter(l=>l.version!==o.version),i=!e.props.of||e.props.of===".";return s`<${re} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${a.statement}</p>`}
    ${a.rationale?s`<p class="rationale prose">${a.rationale}</p>`:null}
    <${hn} predictions=${r?.predictions} />
    ${c.length?s`<${Ue} summary=${`${c.length} earlier version${c.length>1?"s":""}`}>
          ${c.map(l=>s`<p class="small"><code>${l.version}</code> ${l.statement}
            <span class="muted">(${l.runs} runs, check ${l.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function as({node:e}){let t=J("main"),n=e.data?.main.params.group??".",o=t.data?.chain??[],r=o.find(i=>i.group===n)??null,a=o.filter(i=>i.group!==n),c=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${He} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?c:void 0} open=${!1} result=${t}
      action=${s`<${I} spec=${{icon:"circle-help",tone:"muted",label:so}} />`}>
    <${ye} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${pt} text=${i} />`} onSave=${i=>On(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=no)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${a.length?s`<p class="memory-meta small">Memory above this group: ${a.map((i,l)=>s`${l?", ":""}<a href=${S(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var no=5,so="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",oo="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function is({node:e}){let t=J("main"),n=e.data?.main.params.from??".",o=P(t.data).filter(r=>r.path!==n);return s`<${re} title=${e.props.title} count=${t.data?String(o.length):void 0} result=${t}>
    ${t.data&&!o.length?s`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${o.map(r=>{let[a,c]=Dt(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${S(r.path)}
            onPointerEnter=${()=>Ve(r.path)} onFocus=${()=>Ve(r.path)}>
          <${I} spec=${N("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${N("research",r.status).tone}`}>${N("research",r.status).label}</span>`:null}
            ${r.check?s`<${I} spec=${N("result",r.check)} word />`:null}
            ${r.verdict?s`<${I} spec=${N("verdict",r.verdict)} />`:null}
            ${a?s`<span data-tip=${c}>${a}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${I} spec=${N("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${k} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function ls({node:e}){let t=J("main"),n=e.data?.main.params.from??".",[o,r]=y(!1),a=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),c=t.data?.meta?.matched??a.length;return s`<${He} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(c):void 0} result=${t}
      action=${s`<${I} spec=${{icon:"circle-help",tone:"muted",label:oo}} />
        ${s`<${F} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${o?s`<${io} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!a.length&&!o?s`<p class="muted small">No notes yet.</p>`:null}
      ${a.map(i=>s`<${$t} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${cs} call=${e.data.main} before=${a[a.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var ro=20;function cs(e){let[t,n]=y(!1),o=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:ro}}:null,r=w(o);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let a=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${a.map(c=>s`<${$t} key=${c.id} note=${c} scope=${e.scope} />`)}
    ${r.data?.more?s`<${cs} call=${e.call} before=${a[a.length-1]?.id} scope=${e.scope} />`:null}`}var ao=["observation","decision","idea","question","theory"];function ds(e){return(e?.note_types??ao).filter(t=>t!=="verdict")}function io(e){let t=ds(M(he)),[n,o]=y("observation"),[r,a]=y(""),[c,i]=y(""),[l,d]=y(null),[v,m]=y(!1),p=async g=>{if(g.preventDefault(),!r.trim())return d("give the note a title");m(!0);try{await In(e.group,n,r.trim(),c.trim()),e.onDone()}catch(E){d(E.message),m(!1)}};return s`<form class="note new-note" onSubmit=${p} onKeyDown=${g=>{g.key==="Escape"&&e.onDone(),g.key==="Enter"&&(g.metaKey||g.ctrlKey)&&p(g)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${g=>o(g.target.value)}>
        ${t.map(g=>s`<option value=${g}>${g}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${r} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${g=>a(g.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${c} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${g=>i(g.target.value)}></textarea></span>
    <div class="save-actions">
      <${ae} type="submit" icon=${v?"hourglass":"plus"} disabled=${v}>${v?"Adding\u2026":"Add note"}<//>
      <${ae} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${l?s`<span class="bad-text small">${l}</span>`:null}
    </div>
  </form>`}function lo({note:e}){let t=ds(M(he)).filter(n=>n!==e.type);return e.type==="verdict"?s`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${k} name=${N("note","verdict").icon} size=${15} /></span>`:s`<${tt} icon=${N("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>s`<button type="button" key=${n} onClick=${()=>at(e,{type:n})}>
        <${k} name=${N("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function $t(e){let t=e.note,[n,o]=y(!!e.open),[r,a]=y(!1),c=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),l=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${d=>!d.target.closest(".editable, a, .note-delete, .popover-wrap")&&o(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${k} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${lo} note=${t} />
      <${ye} value=${t.description} label="the note's title" class="note-title heading" render=${uo}
        onSave=${d=>at(t,{description:d})} />
      ${t.overall?s`<${I} spec=${N("verdict",t.overall)} />`:null}
      ${t.state?s`<${Ae} tone="warn">${t.state}<//>`:null}
      ${c?s`<a class="note-group small" href=${S(c)} data-tip="from this group">${co(c,e.scope)}</a>`:null}
      <span class="note-meta small">${l?`${l} \xB7 `:""}${W(i)}</span>
      ${s`<${F} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${d=>{d.stopPropagation(),a(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ae} icon="trash" kind="danger" onClick=${()=>{Bn(t)}}>Delete<//>
          <${ae} icon="x" kind="quiet" onClick=${()=>a(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${ye} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${d=>s`<${pt} text=${d} />`}
          onSave=${d=>at(t,{body:d})} />`:null}
  </article>`}function co(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,o=n.split("/").pop()??n;return se(o)?o.slice(-8):n}function us({node:e}){let t=J("main"),n=t.data?.lines??[],o=t.data?.meta??{},r=s`<${k} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${o.total_lines??n.length} lines${(o.shown??0)<(o.total_lines??0)?`, last ${o.shown}`:""}`:""}</span>`;return s`<${re} result=${t}>
    <${Ue} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function ms({node:e}){let t=Y(U);return s`<${re} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ye} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Pe.value===e.id} onCancel=${()=>Pe.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${pt} text=${n} />`}
      onSave=${n=>(Pe.set(null),it(t.path,e.id,n))} />
  <//>`}function ps({node:e}){return s`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function uo(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let o=n.slice(2,-2),[r]=o.split(/[#@]/),a=r.split("/").pop()??"";return s`<a href=${se(a)?oe(a):S(r)}>${o}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function mo(e,t){let n=/^(?:ssh|https?|git):\/\/(?:[^@/]*@)?([^/:]+)(?::\d+)?\/(.+?)(?:\.git)?\/?$/.exec(e??""),o=/^(?:[^@/]+@)?([^/:]+):(?!\/)(.+?)(?:\.git)?\/?$/.exec(e??""),[,r,a]=n??o??[];return!r||!a?null:r==="github.com"?{host:"GitHub",url:`https://github.com/${a}/commit/${t}`}:r==="gitlab.com"||r.startsWith("gitlab.")?{host:"GitLab",url:`https://${r}/${a}/-/commit/${t}`}:null}function ft(e){let{git:t,copied_from:n}=e.run,o=[];return t?.commit&&o.push(["code",s`<${po} git=${t} />`]),n&&o.push(["copied from",s`<a href=${oe(n.id)} data-tip=${`${n.id}, ${n.at}`}>${n.path??n.id}</a>`]),e.checkpoints?.length&&o.push(["checkpoints",s`${e.checkpoints.map(r=>s`<${$o} key=${r.name} ck=${r} />`)}`]),o}function po({git:e}){let t=mo(e.remote,e.commit);return s`<span>${e.commit.slice(0,10)}${e.branch?s` on ${e.branch}`:null}
    ${e.dirty?s` <${Ae} tone="warn" tip="Uncommitted changes when the run started">dirty<//>`:null}
    ${t?s` · <a href=${t.url} target="_blank" rel="noopener noreferrer">${t.host}</a>`:null}</span>`}function $o({ck:e}){let t=()=>{navigator.clipboard?.writeText(e.location)};return s`<div class="checkpoint">
    <span class=${e.exists?"":"muted"} data-tip=${e.location??void 0}>${e.name}</span>
    ${e.exists?null:s`<${Ae} tone="warn" tip=${e.location??void 0}>missing<//> <span class="muted">${fo(e)}</span>`}
    ${e.location?s`<${F} icon="copy" label=${`Copy the path of ${e.name}`} onClick=${t} />`:null}
  </div>`}function fo(e){return e.location?e.via==="origin"?"not found where the source run kept it":"not found at its recorded location":"no location recorded"}function ht({run:e,scope:t}){let[n,o]=y(!1),r=w(n?jn(e,t):null);return s`<${Ue} summary="Uncommitted changes" onToggle=${o}>
    ${r.error?s`<p class="muted small">${r.error}</p>`:null}
    ${r.data?s`<pre class="log code diff">${String(r.data.text).split(`
`).map(a=>s`<span class=${ho(a)}>${a}\n</span>`)}</pre>`:n&&!r.error?s`<div class="skeleton late" style="block-size: 80px"></div>`:null}
  <//>`}function ho(e){return e.startsWith("+++")||e.startsWith("---")||e.startsWith("@@")?"muted":e.startsWith("+")?"tone-good":e.startsWith("-")?"tone-bad":""}function $s(e){let t=()=>R(S(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${k} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${F} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${go} id=${e.run} scope=${e.path} />`:s`<${vo} path=${e.path} />`}
  </aside>`}function go({id:e,scope:t}){let n=w(Le(e,t)).data,o=w(Wn(e,t)).data,r=w(Ge(t)).data,a=w({method:"keys",params:{from:t},scope:t}).data,c=de(),i=Ie(()=>Qe(P(r).map(p=>p["run.id"]),c).get(e),[r,c,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let l=n.run,d=Object.entries(n.metrics??{}),v=tn(i,c),m=ft(n);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${v.class} style=${v.style}></span>
      <a href=${oe(e)}>${l.name}</a></h3>
    <p class="facts small">
      <${I} spec=${ot(l.status,l.exit)} word />
      <span><b>${xe(l.steps)}</b> steps</span>
      <span><b>${Ce(l.duration_s)}</b></span>
      <span data-tip=${l.created_at}>${W(l.created_at)}</span>
    </p>
    ${l.error?s`<pre class="log code bad-text">${l.error}</pre>`:null}
    ${m.length?s`<table class="kv small">${m.map(([p,$])=>s`<tr><td class="muted">${p}</td><td>${$}</td></tr>`)}</table>`:null}
    ${l.git?.dirty?s`<${ht} run=${l.id} scope=${t} />`:null}
    <h4 class="small">Config</h4>
    <${rt} config=${n.config??{}} varying=${je(a)} />
    ${d.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${d.map(([p,$])=>s`<tr><td>${p}</td><td class="num"><b>${ie($.last)}</b></td>
              <td class="num">${ie($.min)}</td><td class="num">${ie($.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(p=>s`<p class="small"><${I} spec=${N("note",p.type)} /> ${p.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(p=>s`<div class="event small"><span class="muted num">${p.t?.slice(5,16).replace("T"," ")}</span>
        <${k} name=${Ct(p.type)} size=${14} /><span>${p.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(o?.lines??[]).join(`
`)}</pre>
  </div>`}function vo({path:e}){let t=w(lt(e)).data,n=w(Gn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(o=>!String(o.state??"").startsWith("superseded")).map(o=>s`<${$t} key=${o.id} note=${o} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(o=>s`<div class="event small"><span class="muted num">${o.t?.slice(5,16).replace("T"," ")}</span>
        <${k} name=${o.kind==="note"?"file-text":Ct(o.type)} size=${14} />
        <span>${o.run?s`<a href=${oe(o.run)}>${o.run.slice(-8)}</a> `:null}${o.description??o.type}</span></div>`)}
  </div>`}function gt(e,t){let n=w(e),o=L(null);return n.status!=="loading"&&(o.current={scope:t,result:n}),n.status==="loading"&&o.current?.scope===t?o.current.result:n}var Pt=null;function fs(e){Pt?.();let t=document.querySelector(".main");if(!e||!t)return;let n=e.getBoundingClientRect().top,o=new ResizeObserver(()=>{e.isConnected&&(t.scrollTop+=e.getBoundingClientRect().top-n)});for(let i of t.children)o.observe(i);let r=["wheel","touchmove","keydown","pointerdown"],a=()=>{o.disconnect(),clearTimeout(c);for(let i of r)removeEventListener(i,a);Pt=null},c=setTimeout(a,5e3);for(let i of r)addEventListener(i,a,{passive:!0});Pt=a}var Rt=["failed","killed","lost"];function Lt(e){let t=ke(e.path),n=t==="."?e.path:e.path.slice(t.length+1),o=G(e.path)?[]:n.split("/"),r=o.length&&se(o[o.length-1])?o[o.length-1]:null,a=o.slice(0,-1),c=i=>[...t==="."?[]:[t],...a.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${o.length?s`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${a.map((i,l)=>s`<span>/</span><a href=${S(c(l))}>${i}</a>`)}
    </nav>
    ${r?s`<${wo} id=${r} scope=${e.path} />`:s`<${bo} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function bo({path:e}){let t=P(w(Re(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let o=Object.entries(w({method:"keys",params:{from:e},scope:e}).data?.codes??{}),r=Rt.reduce((a,c)=>a+(t[c]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${I} spec=${N("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${r?s`<span class="tone-bad" data-tip=${Rt.filter(a=>t[a]).map(a=>`${t[a]} ${a}`).join(", ")}>
            <${k} name="circle-x" size=${15} /> <b>${r}</b> ${r===1?Rt.find(a=>t[a]):"ended early"}</span>`:null}
      ${o.length?s`<span data-tip=${o.map(([a,c])=>`${a}: ${c} run${c===1?"":"s"}`).join(", ")}>
            <${k} name="git-commit" size=${15} /> <b>${o.length}</b> code versions</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${gs} path=${e} />
    </p>`}function hs({path:e}){let t=P(w(Re(e)).data)[0]??null,n=w(t?.proposal?Un(e):null).data,o=w(t?.proposal?Fn(e):null).data;if(!t?.proposal)return null;let r=o?.proposal?.rationale,a=o?.versions?.find(l=>l.version===o.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[c,i]=Dt(n?.progress?.text??t.progress);return s`<${O} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ye} value=${t.proposal} label="the proposal's statement" locked=${o?a:"Loading the proposal\u2026"}
          render=${l=>s`<span data-tip=${a?void 0:r}>${l}</span>`}
          onSave=${l=>zn(e,l)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(l=>{let d=N("result",l.result),v=fn(l),m=v?`${d.label}: ${v}`:d.label;return s`<span class=${`check small tone-${d.tone}`} key=${l.name} data-tip=${m}
              aria-label=${`${l.name}: ${m}`} tabindex="0"><${k} name=${d.icon} size=${14} />${l.name}</span>`})}
        ${n?.provisional||c?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${c?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${c}</span>`:null}
            </span>`:null}
      </div>
      <${yo} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function yo(e){let t=w(e.verdict?lt(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=N("verdict",e.verdict),o=(t?.entries??[]).find(a=>a.type==="verdict"&&(a.group??e.path)===e.path),r=o?be(o.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${k} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${o?s`<span class="small muted" data-tip=${r}>verdict${o.meta?.author?` by ${o.meta.author}`:""}${r?` \xB7 ${W(r)}`:""}</span>`:null}
  </p>`}function wo({id:e,scope:t}){let n=w(Le(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let o=n.run,r=()=>{navigator.clipboard?.writeText(o.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${ye} value=${o.name??o.id} label="the run's name" class="title-edit"
        onSave=${a=>Hn(o.id,t,a.trim())} />
      <${I} spec=${ot(o.status,o.exit)} word /></h1>
    ${o.error?s`<p class="bad-text" data-tip=${o.error}>${o.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${xe(o.steps)}</b> steps</span>
      <span><b>${Ce(o.duration_s)}</b></span>
      ${n.progress?s`<${ko} run=${o} progress=${n.progress} />`:null}
      <span data-tip=${o.created_at}>${W(o.created_at)}</span>
      <${gs} path=${t} />
      <${F} icon="copy" label=${`Copy the run id ${o.id}`} onClick=${r} />
      <${tt} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${[...xo(o),...ft(n)].map(([a,c])=>s`<tr><td class="muted">${a}</td><td>${c}</td></tr>`)}</table>
        ${o.git?.dirty?s`<${ht} run=${o.id} scope=${t} />`:null}
        <div class="menu-list">
          <button type="button" onClick=${()=>R(S(t,{run:o.id}),{replace:!0})}>
            <${k} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${k} name="copy" size=${15} /> Copy the run id</button>
          ${o.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(o.git.commit)}>
            <${k} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(a=>{let c=N("result",a.check);return s`<a class=${`check small tone-${c.tone}`} href=${S(a.group)} data-tip=${a.statement}>
              <${k} name=${c.icon} size=${14} />${a.group==="."?"own proposal":a.group}
              ${a.verdict?s`<${I} spec=${N("verdict",a.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function ko({run:e,progress:t}){let{epoch:n,total:o,fraction:r,steps_per_epoch:a}=t,c=e.status==="running"&&r!==null&&a&&e.steps_per_s?Ce((1-r)*o*a/e.steps_per_s):null;return s`<span>epoch <b>${n}</b>${o?` of ${o}`:""}${r===null?"":` \xB7 ${Math.round(r*100)} % through`}${c?` \xB7 about ${c} left`:""}</span>`}function gs({path:e}){let t=te(e).main,n=gt(Tt(e,t),e).data?.summary;if(!n)return null;let o=Object.entries(n.config??{}).map(([c,i])=>`${xt(c)} ${ie(i)}`).join(", "),r=se(e.split("/").pop()??""),a=`${n.stat} of ${n.metric} over ${r?"the run":"all runs"}${o?` (${o})`:""}`;return s`<span data-tip=${a}>
    best <b>${n.label??xt(`metric.${n.metric}.${n.stat}`)} ${ie(n.value)}</b>
    ${r?null:s` · <a href=${oe(n.run)}>${n.name}</a>`}
  </span>`}function xo(e){return[["id",e.id],["host",e.host],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,o])=>[n,String(o)])}var _t=80;function vs({node:e}){let t=J("main"),n=J(e.data?.keys?"keys":""),o=e.props.mode==="run",r=e.props.title??(o?"Config":"Hyperparameters");return s`<${He} id=${`config:${e.id}`} title=${r} open=${e.props.open} result=${t}>
    ${t.data?o?s`<${rt} config=${t.data.config} varying=${je(n.data)} />`:s`<${Co} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function Co({rows:e}){let t=new Set(je({config:{rows:e}})),n=e.filter(([o])=>t.has(o.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([o,,r])=>{let a=Array.isArray(r)?r.map(ie).join(", "):`${ie(r.min)} \u2026 ${ie(r.max)} \xB7 ${r.distinct} values`;return s`<tr><td data-tip=${o}>${o.replace(/^config\./,"")}</td>
      <td data-tip=${a.length>_t?a:void 0}>${a.length>_t?`${a.slice(0,_t-1)}\u2026`:a}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var bs=15e3;function ys({node:e}){let t=Y(U),n=de(),[o,r]=rn(),a=e.props.code,c=w(r&&a?{method:"code",params:a,scope:null}:null),[i,l]=y(null),[d,v]=y(120),[m,p]=y({error:null,warnings:[]}),$=x=>{me&&console.error(`[block ${e.id}] ${x}`),p(u=>({...u,error:x}))},g=L(()=>{});T(()=>{if(!i)return;p(b=>b.own?{...b,own:!1}:b);let x=!0;Oe.n++;let u=()=>{x&&Oe.n--,x=!1};g.current=u;let f=setTimeout(()=>{x&&$(`no first render within ${bs/1e3} s`),u()},bs);return()=>{clearTimeout(f),u()}},[i]),T(()=>{let x=i?.contentWindow;if(!x||c.status!=="ready")return;let u=D=>x.postMessage(D,"*"),f=new Map,b=new wn,A=D=>{if(D.source!==x)return;let C=D.data;switch(C.type){case"hello":u({type:"init",init:{id:e.id,code:c.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:on.value,pair:Je.value,colormaps:Be.value,prefs:Fe(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics,expanded:e.props.expanded?gn():null}});break;case"sub":if(!vn.has(C.call.method)){u({type:"result",id:C.id,result:{status:"error",data:null,error:`${C.call.method} is not available in a custom block`,refreshing:!1}});break}f.get(C.id)?.(),f.set(C.id,Vt(C.call,ee=>u({type:"result",id:C.id,result:ee})));break;case"unsub":f.get(C.id)?.(),f.delete(C.id);break;case"navigate":C.url.startsWith("/")&&R(C.url);break;case"height":b.accept(performance.now())?v(Math.max(40,C.height)):B("its height keeps changing, so it is fixed at its last height");break;case"chrome":p(ee=>({...ee,own:C.own}));break;case"ready":p(ee=>({...ee,blank:C.blank,overflow:C.overflow})),g.current();break;case"warn":B(C.message);break;case"hover":wt.set(C.run);break;case"prefs":JSON.stringify(H.value)!==JSON.stringify(C.prefs)&&H.set(C.prefs);break;case"download":case"snapshot":C.href?bn(C.href,C.name)?performance.now()-j>1e3&&(j=performance.now(),Ne().download(C.href,C.name)):B(`a download of ${C.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":Ne().figure(C.spec,C.name).catch(ee=>B(`the PDF failed: ${ee.message}`));break;case"expand":yn(C.node)&&Ne().expand(C.node,t);break;case"expand-block":e.props.expanded||Ne().expand(e,t);break;case"close":e.props.expanded&&Me.set(null);break;case"error":$(C.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,E)),g.current();break;default:break}},B=D=>{me&&console.warn(`[block ${e.id}] ${D}`),p(C=>C.warnings.includes(D)?C:{...C,warnings:[...C.warnings,D]})},j=-1/0,H=Fe(t.path),X=wt.subscribe(D=>u({type:"hover",run:D})),_=H.subscribe(D=>u({type:"prefs",prefs:D}));return addEventListener("message",A),u({type:"ping"}),()=>{X(),_(),removeEventListener("message",A);for(let D of f.values())D()}},[c.status,c.data?.code,i]),T(()=>{let x={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(x,"*")},[t.names,t.colors,t.metrics,i]),T(()=>Be.subscribe(x=>i?.contentWindow?.postMessage({type:"colormaps",colormaps:x},"*")),[i]),T(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let E=typeof a=="object"?a.path??a.block:String(a??"");an(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let h=r&&c.status==="ready"&&!m.error;return s`<div ref=${o} class="custom-block">
    ${m.own?null:s`<div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${h?s`<span class="chart-tools">
            <${F} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${F} icon="x" label="Close (Esc)" onClick=${()=>Me.set(null)} />`:s`<${F} icon="maximize" label="Expand" onClick=${()=>Ne().expand(e,t)} />`}
          </span>`:null}
    </div>`}
    <${re} caption=${e.props.expanded?void 0:e.props.caption} result=${c}>
      ${m.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${E})</span>
            <pre class="code">${m.error}</pre>
          </div>`:null}
      ${m.warnings.map(x=>s`<${z} kind="warning">${x}<//>`)}
      ${h?s`<div class="custom-frame" data-frame-blank=${m.blank?"1":void 0} data-frame-overflow=${m.overflow?"1":void 0}>
            <iframe key=${c.data.code} ref=${l} sandbox="allow-scripts" ...${So()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${d}px`} />
          </div>`:null}
    <//>
  </div>`}function So(){if(!!1)return{src:jt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function ws({node:e}){let t=J("main"),n=Y(U),o=t.data?.entries??[];return s`<${re} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!o.length?s`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${o.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Gt(Te(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${ze?"eager":"lazy"} />
          <figcaption class="small">step ${xe(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function ks({node:e}){let t=J("main"),n=t.data?.entries??[];return s`<${re} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${z}>No text logged.<//>`:null}
    ${n.map(o=>s`<div class="text-entry" key=${`${o.run}/${o.step}`}>
        <div class="muted small">step ${xe(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</div>
        <pre class="code">${o.text??""}</pre>
      </div>`)}
  <//>`}function xs({node:e}){let n=`section.${Y(U).path}:${e.id}`,[o,r]=y(()=>ze||ge(n,e.props.open!==!1)),a=()=>{ve(n,!o),r(!o)},c=s`${(e.children??[]).map(d=>s`<${ce} key=${d.id} node=${d} />`)}`,i=Y(et);if(!e.props.title)return s`<div class="stack">${c}</div>`;let l=i===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${o} aria-label=${l?`${o?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${l?`${o?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${a}>
      <${k} name=${o?"chevron-down":"chevron-right"} size=${16} />${l?null:e.props.title}
    </button>
    ${o?s`<div class="stack">${c}</div>`:null}
  </div>`}function Cs({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${ce} key=${n.id} node=${n} />`)}
  </div>`}function Ot({node:e,after:t}){let n=Y(U),o=te(n.path),r=e.props.min_width??320,a=e.props.columns,c=a?`grid-template-columns: repeat(${a}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${r}px, 100%), 1fr))`,i=e.children??[],l=i.filter(m=>o.removed.includes(m.id)).map(m=>m.id),d=$n(i.filter(m=>!l.includes(m.id)),o.order[e.id]),v=(m,p)=>{let $=d.map(g=>g.id).filter(g=>g!==m);if($.splice($.indexOf(p),0,m),mn(n.path,e.id,$),e.id===cn){let g=h=>i.find(x=>x.id===h)?.data?.main?.params?.y?.[0],E=$.map(h=>n.pins.find(x=>x.y===g(h))).filter(h=>!!h);un(n.path,[...E,...n.pins.filter(h=>!E.includes(h))])}};return s`<div class="grid" style=${c}>
    ${d.map(m=>s`<${Eo} key=${m.id} node=${m} path=${n.path} span=${o.spans[m.id]??m.props.span??1}
      columns=${a} onDrop=${p=>p!==m.id&&v(p,m.id)} />`)}
    ${t??null}
    ${l.length?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>We(n.path,l)}>${l.length} hidden · show</button></div>`:null}
  </div>`}var It=[1,2,"full"];function Eo(e){let[t,n]=y(!1),o=It[(It.indexOf(e.span)+1)%It.length],r=a=>a==="full"?"full width":`${a} column${a===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${a=>{a.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${a=>{a.preventDefault(),n(!1),e.onDrop(a.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${a=>a.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${k} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(o)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>pn(e.path,e.node.id,o)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ce} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function zt({root:e}){let t=Y(U),n=te(t.path),o=w({method:"keys",params:{from:t.path},scope:t.path}).data,r=e.props.template;if(!r||!1)return null;let a=new Set(n.removed),c=new Set([...t.charted].filter(([$])=>!a.has($)).flatMap(([,$])=>$)),i=n.added.filter($=>!c.has($)).map($=>({block:"line",id:`added-${$}`,props:{y:$},data:{main:{...r,params:{...r.params,y:[$]}}}})),l=new Set([...c,...i.filter($=>!a.has($.id)).map($=>$.props.y)]),d=(o?.metrics?.rows??[]).map($=>$[0]).filter($=>!l.has($));if(!o||!(d.length||i.length))return null;let v=$=>[...t.charted].find(([g,E])=>a.has(g)&&E.includes($))?.[0]??i.find(g=>a.has(g.id)&&g.props.y===$)?.id,m=$=>{let g=v($);g?We(t.path,[g]):st(t.path,E=>({added:[...E.added,$]}))},p=d.length?s`<div class="add-chart">
        <span class="add-chart-label"><${k} name="plus" size=${16} /> Add a chart</span>
        <${nt} single options=${d} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([$])=>m($)} />
      </div>`:null;return s`<${O}><${Ot} node=${{block:"grid",id:"added",props:{},children:i}} after=${p} /><//>`}function Ss({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[o,r]=y(()=>t.find(i=>i.id===n())?.id??t[0]?.id),a=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},c=t.find(i=>i.id===o)??t[0];return ze?s`<div class="stack">${t.map(i=>s`<${ce} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===c?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>a(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${c?s`<div class="stack" role="tabpanel" id=${`panel-${c.id}`} aria-labelledby=${`tab-${c.id}`}>
          ${(c.children??[]).map(i=>s`<${ce} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var Es={section:xs,row:Cs,grid:Ot,line:Mn,table:Ln,stat:Rn,images:ws,text:ks,proposal:rs,note:ps,output:us,config:vs,memory:as,groups:is,notes:ls,tabs:Ss,scatter:Nn,bar:Dn,histogram:Pn,data_table:Cn,timeline:Sn,custom:ys,markdown:ms},To=new Set(["line","scatter","bar","histogram"]);function ce({node:e}){return To.has(e.block)?s`<${Mo} node=${e} />`:s`<${St} node=${e} blocks=${Es} />`}function Mo({node:e}){let t=Y(U);return te(t.path).removed.includes(e.id)?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>We(t.path,[e.id])}>1 hidden · show</button></div>`:s`<${St} node=${e} blocks=${Es} />`}function Ts(e,t){let n=e.split(`
`),o=t.split(`
`),r=n.length,a=o.length,c=Array.from({length:r+1},()=>new Uint32Array(a+1));for(let v=r-1;v>=0;v--)for(let m=a-1;m>=0;m--)c[v][m]=n[v]===o[m]?c[v+1][m+1]+1:Math.max(c[v+1][m],c[v][m+1]);let i=[],l=0,d=0;for(;l<r&&d<a;)n[l]===o[d]?(i.push({kind:"same",text:n[l]}),l++,d++):c[l+1][d]>=c[l][d+1]?i.push({kind:"removed",text:n[l++]}):i.push({kind:"added",text:o[d++]});for(;l<r;)i.push({kind:"removed",text:n[l++]});for(;d<a;)i.push({kind:"added",text:o[d++]});return i}function Ms(e,t=3){let n=[],o=0;for(;o<e.length;){if(e[o].kind!=="same"){n.push(e[o++]);continue}let r=o;for(;r<e.length&&e[r].kind==="same";)r++;let a=o===0?0:t,c=r===e.length?0:t;r-o>a+c+1?n.push(...e.slice(o,o+a),{kind:"skip",count:r-o-a-c},...e.slice(r-c,r)):n.push(...e.slice(o,r)),o=r}return n}var Bt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function Ns(e){if(Bt[e.block])return Bt[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(r=>Bt[r.block])),[o]=n;if(n.size===1&&o)return o}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function vt(e){let t=w(Ge(e.path)),n=de(),o=P(t.data),r=Ie(()=>Qe(o.map(p=>p["run.id"]),n),[t.data,n]),a=Ie(()=>new Map(o.map(p=>[p["run.id"],p["run.name"]??p["run.id"]])),[t.data]),c=te(e.path),i=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${i}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${O} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let l=e.view.view,d={path:e.path,colors:r,names:a,metrics:e.view.metrics??{},charted:Ht(l),pins:c.main??e.view.pins??[]};if(e.plain)return s`<div class=${i}><${U.Provider} value=${d}><${ce} node=${l} /><//></div>`;let v=l.block==="section"&&!l.props.title?l.children??[]:[l],m=v.map(p=>Ht(p).size>0).lastIndexOf(!0);return s`<div class=${i}>${e.before}
    <${U.Provider} value=${d}>
      ${v.map((p,$)=>{let g=Ns(p);return s`<${Ut} key=${p.id}><${O} label=${g}><${et.Provider} value=${g}><${ce} node=${p} /><//><//>
          ${$===m?s`<${zt} root=${l} />`:null}<//>`})}
      ${m===-1?s`<${zt} root=${l} />`:null}
    <//>
  </div>`}function Ht(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])Ht(n,t);return t}function Ds(e){if(null)return s`<div class="view-source small"><${k} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=M(V),o=n.page==="group"&&n.version,r=t.versions?s`<a href=${S(e.path,{history:!0})}><${k} name="history" size=${14} /> history (${t.versions})</a>`:null,a;switch(t.source){case"draft":a=s`draft <b>${t.draft}</b>`;break;case"view":a=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${W(be(t.version))} by ${t.author??"unknown"}`;break;default:a=s`the built-in view`}return s`<div class="view-source small">
    <${k} name="layout" size=${14} /><span>${a}</span>
    ${o?s`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!o?s`<${No} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||o?null:s`<${Do} path=${e.path} />
        <${Po} path=${e.path} view=${t} />`}
  </div>`}function No(e){let[t,n]=y(null),o=e.outdated.map(a=>a.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await An(e.path)}catch(a){n(a.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${o} exists; update re-pins this view to it (a new version)`}>
      <${k} name="update" size=${14} /> update ${o}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Do(e){let[t,n]=y(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Pe.set(await it(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${k} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Po(e){let t=te(e.path),n=dn(t),[o,r]=y(!1),[a,c]=y(e.view.title??""),[i,l]=y(e.view.finding??""),[d,v]=y(null),[m,p]=y(!1);if(!n&&!o)return null;let $=async g=>{g.preventDefault(),p(!0),v(null);try{let E={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await K("save_view",{path:e.path,prefs:E,title:a,finding:i}),st(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),Ee(h=>["view","view_history","summary"].includes(h.method)&&h.scope===e.path),r(!1)}catch(E){v(E.message)}finally{p(!1)}};return o?s`<form class="save-form" onSubmit=${$}>
    <${Ke} label="Title"><input value=${a} onInput=${g=>c(g.target.value)} /><//>
    <${Ke} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${g=>l(g.target.value)} /><//>
    <div class="save-actions">
      <${ae} type="submit" icon=${m?"hourglass":"save"} disabled=${m}>${m?"Saving\u2026":"Save as view"}<//>
      <${ae} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${d?s`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:s`<${ae} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function Ps(e){let t=w(Xn(e.path)),n=t.data?.entries??[],[o,r]=y(null),a=o??n.slice(0,2).map(i=>i.version).reverse(),c=i=>{let l=a.includes(i)?a.filter(d=>d!==i):[...a,i].slice(-2);r(l.sort())};return t.status==="error"?s`<${z} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${k} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,l)=>s`<li key=${i.version} class=${a.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${a.includes(i.version)} onChange=${()=>c(i.version)} />
            <span class="num muted" data-tip=${i.version}>${W(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${l===0?S(e.path):S(e.path,{version:i.version})}
            onClick=${d=>{d.preventDefault(),R(l===0?S(e.path):S(e.path,{version:i.version}))}}>${l===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${a.length===2?s`<${Ro} path=${e.path} a=${a[0]} b=${a[1]} />`:null}
  </section>`}function Ro(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=w(t(e.a)).data,o=w(t(e.b)).data,r=w($e(e.path,e.a)).data,a=w($e(e.path,e.b)).data,c=n&&o?Ms(Ts(n.yaml,o.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${W(be(e.a))} to ${W(be(e.b))}</h3>
    <pre class="diff code">${c.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${vt} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${a?.title??e.b}</h3><${vt} path=${e.path} view=${a} plain /></div>
    </div>
  </div>`}function Rs(e){return Yn(e.path),e.history?s`<div class="page"><div class="sections">
      <${O} label=${Ls(e.path)}><${Lt} path=${e.path} /><//>
      <${O} label="history"><${Ps} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${Lo} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function Lo(e){let t=te(e.path).main,n=gt($e(e.path,e.version,e.draft,t),`${e.path}|${e.version}|${e.draft}`);T(()=>{n.status==="ready"&&requestAnimationFrame(Zt)},[n.status==="ready"]),T(()=>{let r=a=>fs(a.target.closest?.(".chart-frame")??null);return addEventListener("click",r,!0),()=>removeEventListener("click",r,!0)},[]);let o=s`
    <${O} label=${Ls(e.path)}>
      <${Lt} path=${e.path} finding=${n.data?.finding} />
      ${n.data?s`<${Ds} path=${e.path} view=${n.data} />`:null}
    <//>
    ${se(e.path.split("/").pop()??"")?null:s`<${hs} path=${e.path} />`}`;return n.status==="error"?s`<div class="sections">${o}
      <${O} label="view">
        ${_o(e.path,n.error)?s`<${z} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:s`<${z} kind="error">${n.error}<//>`}
      <//>
    </div>`:s`<${vt} path=${e.path} view=${n.data} before=${o} />`}function Ls(e){return se(e.split("/").pop()??"")?"run":"group"}function _o(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function _s(e){T(()=>{Se($e(e.id)).then(n=>R(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=w($e(e.id));return t.status==="error"?s`<div class="page"><${z} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var Io={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},At=20,_e=-1,Oo=[["day",86400],["week",7*86400],["month",30*86400]];function Os(e){let t=P(w(ue()).data).map(i=>i.path),n=w({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),o=w({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});qe("Timeline",P(n.data).filter(i=>i["run.status"]==="running").length);let r=Date.now()/1e3,a=P(n.data).filter(i=>i["run.created_at"]).map((i,l)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:l})),c=(o.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(be(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${O} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Ke} label="Group" inline>
          <select value=${e.from} onChange=${i=>R(Ye(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${a.length} runs · ${c.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${O} label="runs">
      ${n.status==="error"?s`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&o.data?s`<${zo} bars=${a} marks=${c} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function zo(e){let t=de(),n=L(null),o=[...e.bars.flatMap(h=>[h.start,h.end]),...e.marks.map(h=>h.t)],r=o.length?Is(Math.min(...o),Math.max(...o)):Is(Date.now()/1e3-86400,Date.now()/1e3),[a,c]=y(r),i=e.bars.length,l=Math.min(900,Math.max(160,(i+1.5)*At+40)),v=En(n,Tn,t?(h=>{let x=kn(a[0],a[1]),u=b=>h.colors[Io[b]??"muted"],f=b=>h.colors[b==="verdict"?"good":b==="decision"?"accent":b==="question"?"warn":"muted"];return{style:sn(h),height:l,x:{range:a,log:!1,format:b=>xn(b,x.step),label:"",splits:x.at},y:{range:[_e-.8,i+.5],log:!1,reverse:!0,label:"",size:150,splits:i<=40?[_e,...e.bars.map(b=>b.lane)]:[_e],format:b=>b===_e?"notes":Uo(e.bars[Math.round(b)]?.name??"")},draw:({ctx:b,x:A,y:B,px:j,focused:H})=>{let X=At*.62*j;for(let _ of e.bars){let D=A(_.start),C=Math.max(3*j,A(_.end)-D);b.fillStyle=H!==null&&H!==_.id?nn(u(_.status),.35):u(_.status),b.beginPath(),b.roundRect(D,B(_.lane)-X/2,C,X,3*j),b.fill()}for(let _ of e.marks){let D=A(_.t),C=B(_e),ee=(H===_.id?6:4.5)*j;b.fillStyle=f(_.type),b.beginPath(),b.moveTo(D,C-ee),b.lineTo(D+ee,C),b.lineTo(D,C+ee),b.lineTo(D-ee,C),b.closePath(),b.fill()}},hit:(b,A,B,j)=>{if(Math.abs(A-j(_e))<At/2){let _=Ko(e.marks,D=>Math.abs(B(D.t)-b),8);return _?{key:_.id,rows:Ho(_)}:null}let H=Math.round((A-j(0))/(j(1)-j(0))),X=e.bars.find(_=>_.lane===H&&B(_.start)-3<=b&&b<=Math.max(B(_.end),B(_.start)+3)+3);return X?{key:X.id,rows:Bo(X)}:null},onClick:b=>{let A=e.marks.find(B=>B.id===b);A?R(S(A.group,{drawer:!0})):R(oe(b))}}})(t):null,[a,e.bars,e.marks],t),m=h=>{if(!v.current)return;h.preventDefault();let x=v.current.xAt(h.clientX),u=Math.exp(h.deltaY*.0015);c(([f,b])=>Kt([x-(x-f)*u,x+(b-x)*u],r))},p=L(null),$=h=>p.current={x:h.clientX,range:a},g=h=>{if(!p.current||!v.current||!(h.buttons&1))return;let x=(h.clientX-p.current.x)*v.current.xPerPixel(),[u,f]=p.current.range;Math.abs(h.clientX-p.current.x)>3&&c(Kt([u-x,f-x],r))},E=Math.max(...o,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Oo.map(([h,x])=>s`<button type="button" role="radio" aria-checked=${Math.abs(a[1]-a[0]-x)<1}
          onClick=${()=>c(Kt([E-x,E+x*.02],[Math.min(r[0],E-x),r[1]]))}>last ${h}</button>`)}
      <button type="button" role="radio" aria-checked=${a[0]===r[0]&&a[1]===r[1]} onClick=${()=>c(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${l}px`}
      onWheel=${m} onPointerDown=${$} onPointerMove=${g} onPointerUp=${()=>p.current=null}></div>
    <p class="muted small">${Ao(t)}</p>
  </div>`}function Bo(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:W(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Ce(e.end-e.start),color:null}]}function Ho(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:W(new Date(e.t*1e3).toISOString()),color:null}]}function Ao(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Ko(e,t,n){let o=null,r=n;for(let a of e){let c=t(a);c<r&&([o,r]=[a,c])}return o}function Is(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Kt([e,t],n){let o=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-o));return[r,r+o]}function Uo(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function zs(){let e=M(Me),t=L(null);if(T(()=>{let r=t.current;if(!r||!e)return;r.showModal();let a=()=>Me.set(null);return r.addEventListener("close",a),()=>r.removeEventListener("close",a)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},o=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${o} closedby="any">
    <${U.Provider} value=${e.view}><${ce} node=${n} /><//>
  </dialog>`}function Bs(e,t){let n=e.toLowerCase(),o=t.toLowerCase();if(!n)return 1;let r=o.indexOf(n);if(r>=0)return 100-Math.min(r,50)-o.length/100;let a=0,c=0;for(let i of o)if(i===n[a]?a++:a>0&&c++,a===n.length)return 40-Math.min(c,39);return 0}function As(e){let[t,n]=y(e.query),[o,r]=y(0),a=L(null),c=P(w(ue()).data),i=P(w(ct()).data);T(()=>{let u=a.current;u.showModal();let f=()=>Q.set(null);u.addEventListener("close",f);let b=!1,A=H=>{let X=u.getBoundingClientRect();return H.clientX<X.left||H.clientX>X.right||H.clientY<X.top||H.clientY>X.bottom},B=H=>b=A(H),j=H=>b&&A(H)&&u.close();return"closedBy"in HTMLDialogElement.prototype||(u.addEventListener("pointerdown",B),u.addEventListener("pointerup",j)),()=>{u.removeEventListener("close",f),u.removeEventListener("pointerdown",B),u.removeEventListener("pointerup",j)}},[]);let l=()=>a.current?.close(),d=u=>()=>R(u),v=V.value,m=v.page==="group"?v.path:".",p=(u,f,b,A)=>({section:"Commands",label:u,detail:f,sym:{icon:b,tone:"muted",label:u},run:A}),g=[...c.map(u=>({section:"Groups",label:u.path==="."?"local":u.path,detail:`${u.runs} runs${u.proposal?` \xB7 ${u.proposal}`:""}`,sym:N("research",u.status),run:d(S(u.path))})),...i.map(u=>({section:"Runs",label:u["run.name"]??u["run.id"],detail:`${u["run.status"]} \xB7 ${u["run.path"]}`,sym:N("run",u["run.status"]),run:d(S(u["run.path"]))})),p("Theme: light","","sun",()=>Ze("light")),p("Theme: dark","","moon",()=>Ze("dark")),p("Theme: follow the system","","monitor",()=>Ze("system")),p("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),p("Show notes and timeline","i","file-text",d(S(m,{drawer:!0}))),p("Show or hide the sidebar","\u2318B","panel-left",()=>Z.set(!Z.value)),p(ne.value?"Resume live updates":"Pause live updates","p",ne.value?"play":"pause",()=>ne.set(!ne.value)),p("Keyboard shortcuts","?","keyboard",()=>fe.set(!0)),p("Settings","","settings",d("/settings/appearance"))].map(u=>({it:u,s:Math.max(Bs(t,u.label),Bs(t,u.detail)*.5)})).filter(u=>u.s>0).sort((u,f)=>f.s-u.s||Hs(u.it.section)-Hs(f.it.section)).slice(0,60).map(u=>u.it),E=u=>{u&&(l(),u.run())},h=u=>{if(u.key==="ArrowDown")r(Math.min(g.length-1,o+1));else if(u.key==="ArrowUp")r(Math.max(0,o-1));else if(u.key==="Enter")E(g[o]);else return;u.preventDefault()},x="";return s`<dialog class="sheet" ref=${a} aria-label="Search" closedby="any">
    <div class="palette-input"><${k} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${g[o]?`pal-${o}`:void 0}
        onInput=${u=>{n(u.target.value),r(0)}} onKeyDown=${h} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${g.map((u,f)=>{let b=u.section!==x&&!t?x=u.section:null;return s`${b?s`<li class="palette-head small" role="presentation">${b}</li>`:null}
          <li id=${`pal-${f}`} class="item" role="option" aria-selected=${f===o}
              onMouseMove=${()=>r(f)} onClick=${()=>E(u)}>
            <${I} spec=${u.sym} /><span class="label">${u.label}</span><span class="detail small">${u.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function Hs(e){return["Groups","Runs","Commands"].indexOf(e)}function bt(e,t=[]){let n=new Map,o=(i,l={})=>({path:i,name:i==="."?"local":i.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let i of e)n.set(i.path,o(i.path,i));(t.length===0||t.some(i=>i.name==="local"))&&!n.has(".")&&n.set(".",o("."));for(let i of t){let l=i.name==="local"?".":i.name;n.has(l)||n.set(l,o(l)),Object.assign(n.get(l),{state:i.state,error:i.error})}for(let i of n.values()){if(G(i.path))continue;let l=i.path.lastIndexOf("/"),d=l<0?".":i.path.slice(0,l);(n.get(d)??n.get(ke(i.path))??n.get(".")).children.push(i)}for(let i of n.values())i.children.sort((l,d)=>l.name.localeCompare(d.name));let a=[...n.values()].filter(i=>i.path!=="."&&G(i.path)).sort((i,l)=>i.name.localeCompare(l.name)),c=n.get(".");return c?[c,...a]:a}function Ks(e,t,n,o=new Set){let r=[],a=n.toLowerCase(),c=i=>{(!a||i.path.toLowerCase().includes(a)||Us(i,a))&&(r.push(i),(a||(G(i.path)?!o.has(i.path):t.has(i.path)))&&i.children.forEach(c))};return e.forEach(c),r}function Us(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Us(n,t))}function Fs(e,t){if(G(t))return e;let n=t.lastIndexOf("/"),o=n<0?".":t.slice(0,n),r=a=>a.path===o?a:a.children.map(r).find(c=>c)??null;return e.map(r).find(a=>a)?.children??[]}function Ws(e){return G(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function js(){let e=M(V),t=w(ue()),[n,o]=y(()=>new Set(ge("open",[]))),[r,a]=y(()=>new Set(ge("closed-hosts",[]))),[c,i]=y(""),l=L(null),d=e.page==="group"?e.path:null,v=bt(P(t.data),t.data?.meta?.sources??[]),m=Ks(v,jo(n,d),c,r),p=h=>G(h)?!r.has(h):n.has(h),$=(h,x)=>{let u=x??!p(h);if(G(h)){let b=new Set(r);u?b.delete(h):b.add(h),ve("closed-hosts",[...b]),a(b);return}let f=new Set(n);u?f.add(h):f.delete(h),ve("open",[...f]),o(f)},g=L(d);return T(()=>{d!==g.current&&d&&!G(d)&&r.has(ke(d))&&$(ke(d),!0),g.current=d},[d]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${k} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${c} aria-label="Filter groups"
        onInput=${h=>i(h.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${h=>{let x=[...l.current?.querySelectorAll("a.tree-item")??[]],u=x.indexOf(document.activeElement),f=m[u];switch(h.key){case"ArrowDown":x[Math.min(x.length-1,u+1)]?.focus();break;case"ArrowUp":x[Math.max(0,u-1)]?.focus();break;case"ArrowRight":f?.children.length&&$(f.path,!0);break;case"ArrowLeft":f?.children.length&&p(f.path)?$(f.path,!1):f&&x[m.findIndex(b=>b.path===Wo(f.path))]?.focus();break;default:return}h.preventDefault()}} role="tree">
      ${m.map(h=>s`<${Fo} key=${h.path} node=${h} current=${h.path===d}
        open=${p(h.path)||!!c} onToggle=${()=>$(h.path)} />`)}
    </div>
  </nav>`}function Fo(e){let t=e.node,n=()=>Ve(t.path),o=t.children.length>0,r=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${G(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${o?e.open:void 0}
      style=${`padding-inline-start:${8+Ws(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${a=>{a.metaKey||a.ctrlKey||(a.preventDefault(),R(S(t.path)))}}>
    <span class="twisty" onClick=${a=>{a.preventDefault(),a.stopPropagation(),e.onToggle()}}>
      ${o?s`<${k} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${G(t.path)?s`<${I} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${I} spec=${N("run","running")} size=${14} />`:null}
      ${t.failed?s`<${I} spec=${{...N("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Wo(e){if(G(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function jo(e,t){if(!t||t===".")return e;let n=new Set(e),o=t.split("/");for(let r=1;r<o.length;r++)n.add(o.slice(0,r).join("/"));return n}function Vs(){let e=M(V),t=M(Z),n=M(Q),o=M(fe),r=L(null);T(()=>Jt(()=>r.current),[]),T(()=>(addEventListener("keydown",Gs),()=>removeEventListener("keydown",Gs)),[]);let a=e.page==="group"&&e.drawer,c;switch(e.page){case"group":c=s`<${Rs} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":c=s`<${_s} id=${e.id} />`;break;case"settings":c=s`<${es} />`;break;case"timeline":c=s`<${Os} key=${e.from} from=${e.from} />`;break;default:c=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return me||!1?s`<main class="main render-main" ref=${r}>${c}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${a?" with-drawer":""}`}>
    <${ns} />
    ${t?s`<${js} />`:null}
    <main class="main" ref=${r}>${c}</main>
    ${a?s`<${$s} path=${e.path} run=${e.run} />`:null}
    <${ss} />
    ${n!==null?s`<${As} query=${n} />`:null}
    ${o?s`<${Vo} />`:null}
    <${zs} />
  </div>`}function Gs(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),Q.set(Q.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Z.set(!Z.value);return}if(e.key==="Escape"){if(Q.value!==null||fe.value)return;let o=V.value;return o.page==="group"&&o.run?R(S(o.path,{drawer:!0}),{replace:!0}):o.page==="group"&&o.drawer?R(S(o.path),{replace:!0}):void 0}if(t||e.altKey||Zn(e)||Q.value!==null||fe.value)return;let n=V.value;switch(e.key){case"/":e.preventDefault(),Q.set("");break;case"?":fe.set(!fe.value);break;case"p":ne.set(!ne.value);break;case"i":n.page==="group"&&R(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Z.set(!Z.value);break;case"[":case"]":n.page==="group"&&Go(n.path,e.key==="]"?1:-1);break}}async function Go(e,t){let n=await Se(ue()),o=Fs(bt(P(n),n?.meta?.sources??[]),e),r=o.findIndex(c=>c.path===e),a=o[r+t];a&&R(S(a.path))}function Vo(){let e=L(null);return T(()=>{let t=e.current;t.showModal();let n=()=>fe.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${ut.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ae} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Qt();if(me){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(pe.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Oe.n,en&&ln()}_n();var qo=K("meta").then(e=>(me&&(e={...e,settings:{...e.settings,theme_mode:pe.value}}),mt(e),e));!me&&!!1&&Yt(async()=>{let[e,t]=await Promise.all([qo,K("meta")]);e.bundle!==t.bundle?location.reload():mt(t)});Ft(s`<${Vs} />`,document.getElementById("app"));
