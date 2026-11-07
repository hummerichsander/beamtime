import{$ as oe,A as zt,Aa as Jt,B as Bt,Ba as gt,C as Se,Ca as Ze,D as te,Da as Qe,E as S,Ea as Zt,F as je,Fa as Qt,G as de,Ga as en,H as _e,Ha as tn,I as be,Ia as nn,J as G,K as W,L as At,La as sn,Ma as an,N as L,Na as rn,O as Ht,Oa as cn,P as Kt,Pa as dn,Q as ue,Qa as un,R as Re,S as Ut,Sa as mn,T as Ge,Ta as pn,U as mt,Ua as $n,V as me,Va as fn,W as Vt,Wa as hn,X as pt,Xa as gn,Y as Ve,Ya as vn,Z as Y,Za as bn,_ as J,aa as We,ba as Wt,c as Lt,ca as Ie,d as s,da as Oe,e as g,f as T,fa as qt,g as Pt,ga as Xt,h as I,ha as b,i as Le,ia as _,j as ce,ja as qe,ka as ne,la as O,m as ve,ma as D,n as M,na as ze,o as we,oa as V,p as ke,pa as Yt,qa as z,ra as se,s as K,sa as Be,t as Pe,ta as $t,u as xe,ua as Xe,v as ut,va as Ye,w as y,wa as E,x as It,xa as ht,y as ee,ya as Ae,z as Ot,za as Je}from"./chunks/chunk-RTFYDR5I.js";import{a as _t,b as Rt}from"./chunks/chunk-O2K4N3UR.js";import{C as on,D as ln,e as Ft,i as jt,j as Gt,k as F,n as he,o as ye,p as Ce,q as U,r as ft}from"./chunks/chunk-C3Y3QD3X.js";import"./chunks/chunk-VC46IEJQ.js";function Ee(e,t){Se(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var vt=["notes","timeline","groups","check","card","memory_show","status"];async function et(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Ee(e.group,vt)}async function yn(e,t,n,a){await K("note_add",{group:e,type:t,description:n,body:a}),Ee(e,vt)}async function wn(e,t){await K("memory_update",{group:e,body:t}),Ee(e,["memory_show","status"])}async function kn(e,t){let n=await K("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await K("proposal_set",{group:e,proposal:{...a,statement:t}}),Ee(e,["groups","proposal_show","check","summary"])}async function xn(e){await K("note_rm",{note:e.id}),Ee(e.group,vt)}async function Sn(e,t,n){await K("name",{run:e,name:n}),Ee(t,["card","runs","groups","summary","series"])}async function tt(e,t,n){let a=await K("view_text",{path:e,id:t,text:n});return Se(r=>["view","view_history"].includes(r.method)&&r.scope===e),a.id}async function Cn(e){await K("view_upgrade",{group:e}),Se(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Te=new ve(null);async function En(e,t){return await K("set",{key:e,value:t}),K("meta")}var ie=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),pe=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),bt=e=>({method:"summary",params:{path:e},scope:e}),Me=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Tn=e=>({method:"check",params:{group:e},scope:e}),Mn=e=>({method:"proposal_show",params:{group:e},scope:e}),Ne=(e,t)=>({method:"card",params:{run:_e(e,t)},scope:t}),Nn=(e,t)=>({method:"output",params:{run:_e(e,t),tail:30},scope:t}),He=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),nt=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Dn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Ln=()=>({method:"status",params:{},scope:"."}),st=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ke(e){for(let t of[pe(e),Me(e),He(e),bt(e)])ut(t);xe(pe(e)).then(t=>{for(let n of Pn(t.view))ut(n)}).catch(()=>{})}function Pn(e){return e?[...Ls.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(Pn)]:[]}var Ls=new Set(["line","custom"]),_n=e=>({method:"view_history",params:{group:e},scope:e});var yt="/static/favicon.svg",at=null;async function Ps(){if(at)return at;let e=new Image;e.src=yt,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let a=n.getContext("2d");if(!a)return yt;a.drawImage(e,0,0,t,t),a.beginPath(),a.arc(t-6,t-6,6,0,Math.PI*2);let r=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return a.fillStyle=r||"#2f5aa8",a.fill(),at=n.toDataURL("image/png"),at}function _s(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=yt;return}Ps().then(n=>{t.type="image/png",t.href=n})}}function Ue(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,_s(t>0)},[e,t])}function Rn(e){let t=te(e.split("/").pop()??""),n=y(t?null:Me(e)),a=y(t?Ne(e.split("/").pop()??"",e):null),r=t?a.data?.run.name??a.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,o=t?a.data?.run.status==="running"?1:0:D(n.data)[0]?.running??0;Ue(r,o)}var Z=new ve(we("sidebar",!0)),Q=new ve(null),$e=new ve(!1),fe=new ve(null);Z.subscribe(e=>ke("sidebar",e));var In=we("visit",Date.now());ke("visit",Date.now());function On(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var rt=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Rs=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function ot(e){fe.set(e),Ge.set(e.theme),e.settings?.theme_mode&&me.set(e.settings.theme_mode),pt()}var zn=0;async function wt(e,t){let n=++zn;e==="theme_mode"&&(me.set(t),pt());let a=await En(e,t);n===zn&&ot(a)}function Bn(){let e=M(me),t=oe(),n=M(fe),[a,r]=g(null);Ue("Settings");let o=(l,u)=>{r(null),wt(l,u).catch(m=>r(m.message))},c=n?.settings??{},i=(l,u,m)=>s`
    <label class="field-label small" for=${`setting-${l}`}>${u}</label>
    <span class="input body">
      <select id=${`setting-${l}`} value=${c[l]} onChange=${p=>o(l,p.target.value)}>
        ${m.map(p=>s`<option value=${p}>${p}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${z} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${c.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${a?s`<${O} kind="error">${a}<//>`:null}
    <//>
    <${z} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Rs.map(([l,u,m])=>s`<button type="button" role="radio" aria-checked=${e===l} onClick=${()=>o("theme_mode",l)}>
            <${b} name=${u} size=${15} />${m}</button>`)}
        </div>
        ${i("theme","Theme",n?.themes??[])}
        ${i("colormap","Colormap",n?.colormaps?.sequential??[])}
        ${i("colormap_diverging","Diverging colormap",n?.colormaps?.diverging??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps color numeric groups and heatmaps.</p>
      ${(n?.theme?.problems??[]).map(l=>s`<${O} kind="warning">${l}<//>`)}
    <//>
    <${z} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${Ye} options=${n.figure_styles} value=${c.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${l=>o("figure_style",l)} />`:s`<span class="muted small"><code>${JSON.stringify(c.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(c.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${z} label="keyboard">
      <table class="kv">${rt.map(([l,u])=>s`<tr><td><kbd class="small">${l}</kbd></td><td>${u}</td></tr>`)}</table>
    <//>
    <${z} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(l=>s`
          <tr><td class="muted">${l.name}</td><td><code class="code">${l.logdir}</code> (${l.kind}, ${l.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var An={system:"light",light:"dark",dark:"system"},Is={system:"monitor",light:"sun",dark:"moon"};function Hn(){let e=M(fe),t=M(me),n=M(Z);return s`<header class="topbar">
    <${V} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Z.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>Q.set("")} aria-label="Search (⌘K)">
      <${b} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Os} />
      <${V} icon=${Is[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${An[t]})`}
        onClick=${()=>{wt("theme_mode",An[t])}} />
      <a class="icon-button" href=${je(W.value.page==="group"?W.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${b} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${b} name="settings" size=${16} /></a>
    </div>
  </header>`}function Os(){let t=(y(ie()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${S(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${b} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${b} name="server" size=${15} /> local</span>`}function zs(e){let[t,n]=g(Date.now());return T(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function Bs(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function Kn(){let e=M(Ot),t=M(ee),n=M(zt),a=M(W),r=zs(5e3),o=y(Ln()).data,c=D(y(st()).data),i=M(fe),l=o?.daemon,u=o?.runs?.running??0,m=c.filter(P=>P["run.status"]==="failed"&&Bs(P["run.ended_at"])>In).length,p=o?.meta?.freshness,[v,C,x]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&l?["",`live \xB7 updated ${U(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${l.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${x}><span class=${`live-dot ${v}`}></span>${C}</span>
    ${u?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>Q.set("running")}>
          <${b} name="circle-dot" size=${14} class="tone-accent" />${u} running</button>`:null}
    ${m?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>Q.set("failed")}>
          <${b} name="circle-x" size=${14} />${m} failed since your last visit</button>`:null}
    ${p?.behind?s`<span class="status-item warn-text" data-tip=${p.text}><${b} name="hourglass" size=${14} />${p.behind} runs behind</span>`:null}
    ${p?.damaged?.length?s`<span class="status-item warn-text" data-tip=${p.damaged.join(`
`)}><${b} name="triangle-alert" size=${14} />${p.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${b} name="activity" size=${14} />1 run selected</span>`:null}
    <${V} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ee.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var Un=null;function it(e){let t=I(null),[n,a]=g(null),[r,o]=g(!1),[c,i]=g(!1);T(()=>{let p=!0;return Un??=import("./chunks/md-SW3VT2BQ.js"),Un.then(v=>v.render(e.text??"")).then(v=>p&&a(v)),()=>{p=!1}},[e.text]),Pt(()=>{let p=t.current;if(!p||!e.clamp)return;let v=()=>i(p.scrollHeight>p.clientHeight+2),C=new ResizeObserver(v);return C.observe(p),()=>C.disconnect()},[e.clamp,n]);let l=e.clamp&&!r,u=`md${l?" clamped":""}`,m=l?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${u} ref=${t} style=${m}>
          ${(e.text??"").split(/\n{2,}/).map(p=>s`<p>${p}</p>`)}
        </div>`:s`<div class=${u} ref=${t} style=${m} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(c||r)?s`<button type="button" class="link small more" onClick=${()=>o(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function ge(e){let[t,n]=g(!!e.startEditing),[a,r]=g(e.value),[o,c]=g(null),[i,l]=g(null),u=I(null),m=I(!1);T(()=>c(null),[e.value]),T(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[p,v]=g(!1),C=e.locked??void 0,x=$=>{if(!$.target.closest("a, button, input, summary")){if(C)return v(!0);$.preventDefault(),r(o??e.value),l(null),m.current=!1,n(!0)}},P=()=>{m.current=!0,n(!1),l(null),e.onCancel?.()},f=async()=>{if(m.current)return;m.current=!0;let $=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if($===e.value.trim()||!$&&!e.multiline)return P();n(!1),c($);try{await e.onSave($)}catch(h){c(null),r($),l(h.message),m.current=!1,n(!0)}},w=$=>{if($.key==="Escape")return $.preventDefault(),$.stopPropagation(),P();$.key!=="Enter"||$.isComposing||$.keyCode===229||(!e.multiline||$.metaKey||$.ctrlKey)&&($.preventDefault(),f())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
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
  </div>`}function kt(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${F(e.ci[0])}, ${F(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${F(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${F(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function xt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function Fn({node:e}){let t=J("proposal"),n=J("check"),a=t.data,r=n.data;if(!a)return s`<${ne} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let o=a.proposal??{},c=(a.versions??[]).filter(l=>l.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${ne} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${o.statement}</p>`}
    ${o.rationale?s`<p class="rationale prose">${o.rationale}</p>`:null}
    <div class="predictions">
      ${(r?.predictions??[]).map(l=>s`<div class="prediction" key=${l.name}>
          <${_} spec=${E("result",l.result)} />
          <span class="pname">${l.name}</span>
          <span class="pdetail num small">${kt(l)}</span>
        </div>`)}
    </div>
    ${c.length?s`<${$t} summary=${`${c.length} earlier version${c.length>1?"s":""}`}>
          ${c.map(l=>s`<p class="small"><code>${l.version}</code> ${l.statement}
            <span class="muted">(${l.runs} runs, check ${l.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function jn({node:e}){let t=J("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],r=a.find(i=>i.group===n)??null,o=a.filter(i=>i.group!==n),c=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${ze} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?c:void 0} open=${!1} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:Hs}} />`}>
    <${ge} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${it} text=${i} />`} onSave=${i=>wn(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=As)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${o.length?s`<p class="memory-meta small">Memory above this group: ${o.map((i,l)=>s`${l?", ":""}<a href=${S(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var As=5,Hs="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Ks="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function Gn({node:e}){let t=J("main"),n=e.data?.main.params.from??".",a=D(t.data).filter(r=>r.path!==n);return s`<${ne} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${O}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(r=>{let[o,c]=xt(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${S(r.path)}
            onPointerEnter=${()=>Ke(r.path)} onFocus=${()=>Ke(r.path)}>
          <${_} spec=${E("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${E("research",r.status).tone}`}>${E("research",r.status).label}</span>`:null}
            ${r.check?s`<${_} spec=${E("result",r.check)} word />`:null}
            ${r.verdict?s`<${_} spec=${E("verdict",r.verdict)} />`:null}
            ${o?s`<span data-tip=${c}>${o}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${_} spec=${E("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${b} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Vn({node:e}){let t=J("main"),n=e.data?.main.params.from??".",[a,r]=g(!1),o=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),c=t.data?.meta?.matched??o.length;return s`<${ze} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(c):void 0} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:Ks}} />
        ${s`<${V} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${js} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!o.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${o.map(i=>s`<${lt} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Wn} call=${e.data.main} before=${o[o.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Us=20;function Wn(e){let[t,n]=g(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Us}}:null,r=y(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let o=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${o.map(c=>s`<${lt} key=${c.id} note=${c} scope=${e.scope} />`)}
    ${r.data?.more?s`<${Wn} call=${e.call} before=${o[o.length-1]?.id} scope=${e.scope} />`:null}`}var Fs=["observation","decision","idea","question","theory"];function qn(e){return(e?.note_types??Fs).filter(t=>t!=="verdict")}function js(e){let t=qn(M(fe)),[n,a]=g("observation"),[r,o]=g(""),[c,i]=g(""),[l,u]=g(null),[m,p]=g(!1),v=async x=>{if(x.preventDefault(),!r.trim())return u("give the note a title");p(!0);try{await yn(e.group,n,r.trim(),c.trim()),e.onDone()}catch(P){u(P.message),p(!1)}};return s`<form class="note new-note" onSubmit=${v} onKeyDown=${x=>{x.key==="Escape"&&e.onDone(),x.key==="Enter"&&(x.metaKey||x.ctrlKey)&&v(x)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${x=>a(x.target.value)}>
        ${t.map(x=>s`<option value=${x}>${x}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${r} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${x=>o(x.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${c} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${x=>i(x.target.value)}></textarea></span>
    <div class="save-actions">
      <${se} type="submit" icon=${m?"hourglass":"plus"} disabled=${m}>${m?"Adding\u2026":"Add note"}<//>
      <${se} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${l?s`<span class="bad-text small">${l}</span>`:null}
    </div>
  </form>`}function Gs({note:e}){let t=qn(M(fe)).filter(n=>n!==e.type);return e.type==="verdict"?s`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${b} name=${E("note","verdict").icon} size=${15} /></span>`:s`<${Xe} icon=${E("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>s`<button type="button" key=${n} onClick=${()=>et(e,{type:n})}>
        <${b} name=${E("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function lt(e){let t=e.note,[n,a]=g(!!e.open),[r,o]=g(!1),c=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),l=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete, .popover-wrap")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${b} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${Gs} note=${t} />
      <${ge} value=${t.description} label="the note's title" class="note-title heading" render=${Ws}
        onSave=${u=>et(t,{description:u})} />
      ${t.overall?s`<${_} spec=${E("verdict",t.overall)} />`:null}
      ${t.state?s`<${Yt} tone="warn">${t.state}<//>`:null}
      ${c?s`<a class="note-group small" href=${S(c)} data-tip="from this group">${Vs(c,e.scope)}</a>`:null}
      <span class="note-meta small">${l?`${l} \xB7 `:""}${U(i)}</span>
      ${s`<${V} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${u=>{u.stopPropagation(),o(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${se} icon="trash" kind="danger" onClick=${()=>{xn(t)}}>Delete<//>
          <${se} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${ge} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${u=>s`<${it} text=${u} />`}
          onSave=${u=>et(t,{body:u})} />`:null}
  </article>`}function Vs(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return te(a)?a.slice(-8):n}function Xn({node:e}){let t=J("main"),n=t.data?.lines??[],a=t.data?.meta??{},r=s`<${b} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${ne} result=${t}>
    <${$t} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Yn({node:e}){let t=ce(Y);return s`<${ne} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ge} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Te.value===e.id} onCancel=${()=>Te.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${it} text=${n} />`}
      onSave=${n=>(Te.set(null),tt(t.path,e.id,n))} />
  <//>`}function Jn({node:e}){return s`<${O} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Ws(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[r]=a.split(/[#@]/),o=r.split("/").pop()??"";return s`<a href=${te(o)?de(o):S(r)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function Zn(e){let t=()=>L(S(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${b} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${V} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${qs} id=${e.run} scope=${e.path} />`:s`<${Xs} path=${e.path} />`}
  </aside>`}function qs({id:e,scope:t}){let n=y(Ne(e,t)).data,a=y(Nn(e,t)).data,r=y(He(t)).data,o=y({method:"keys",params:{from:t},scope:t}).data,c=oe(),i=Le(()=>We(D(r).map(p=>p["run.id"]),c).get(e),[r,c,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let l=n.run,u=Object.entries(n.metrics??{}),m=Ft(i,c);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${m.class} style=${m.style}></span>
      <a href=${de(e)}>${l.name}</a></h3>
    <p class="facts small">
      <${_} spec=${E("run",l.status)} word />
      <span><b>${ye(l.steps)}</b> steps</span>
      <span><b>${Ce(l.duration_s)}</b></span>
      <span data-tip=${l.created_at}>${U(l.created_at)}</span>
    </p>
    ${l.error?s`<pre class="log code bad-text">${l.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <${Je} config=${n.config??{}} varying=${Ae(o)} />
    ${u.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${u.map(([p,v])=>s`<tr><td>${p}</td><td class="num"><b>${F(v.last)}</b></td>
              <td class="num">${F(v.min)}</td><td class="num">${F(v.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(p=>s`<p class="small"><${_} spec=${E("note",p.type)} /> ${p.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(p=>s`<div class="event small"><span class="muted num">${p.t?.slice(5,16).replace("T"," ")}</span>
        <${b} name=${ht(p.type)} size=${14} /><span>${p.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function Xs({path:e}){let t=y(nt(e)).data,n=y(Dn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${lt} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${b} name=${a.kind==="note"?"file-text":ht(a.type)} size=${14} />
        <span>${a.run?s`<a href=${de(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var St=["failed","killed","lost"];function Ct(e){let t=be(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=G(e.path)?[]:n.split("/"),r=a.length&&te(a[a.length-1])?a[a.length-1]:null,o=a.slice(0,-1),c=i=>[...t==="."?[]:[t],...o.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${o.map((i,l)=>s`<span>/</span><a href=${S(c(l))}>${i}</a>`)}
    </nav>
    ${r?s`<${Zs} id=${r} scope=${e.path} />`:s`<${Ys} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function Ys({path:e}){let t=D(y(Me(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=St.reduce((r,o)=>r+(t[o]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${_} spec=${E("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${St.filter(r=>t[r]).map(r=>`${t[r]} ${r}`).join(", ")}>
            <${b} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?St.find(r=>t[r]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${es} path=${e} />
    </p>`}function Qn({path:e}){let t=D(y(Me(e)).data)[0]??null,n=y(t?.proposal?Tn(e):null).data,a=y(t?.proposal?Mn(e):null).data;if(!t?.proposal)return null;let r=a?.proposal?.rationale,o=a?.versions?.find(l=>l.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[c,i]=xt(n?.progress?.text??t.progress);return s`<${z} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ge} value=${t.proposal} label="the proposal's statement" locked=${a?o:"Loading the proposal\u2026"}
          render=${l=>s`<span data-tip=${o?void 0:r}>${l}</span>`}
          onSave=${l=>kn(e,l)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(l=>{let u=E("result",l.result),m=kt(l),p=m?`${u.label}: ${m}`:u.label;return s`<span class=${`check small tone-${u.tone}`} key=${l.name} data-tip=${p}
              aria-label=${`${l.name}: ${p}`} tabindex="0"><${b} name=${u.icon} size=${14} />${l.name}</span>`})}
        ${n?.provisional||c?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${c?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${c}</span>`:null}
            </span>`:null}
      </div>
      <${Js} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Js(e){let t=y(e.verdict?nt(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=E("verdict",e.verdict),a=(t?.entries??[]).find(o=>o.type==="verdict"&&(o.group??e.path)===e.path),r=a?he(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${b} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${r}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${r?` \xB7 ${U(r)}`:""}</span>`:null}
  </p>`}function Zs({id:e,scope:t}){let n=y(Ne(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,r=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${ge} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${o=>Sn(a.id,t,o.trim())} />
      <${_} spec=${E("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${ye(a.steps)}</b> steps</span>
      <span><b>${Ce(a.duration_s)}</b></span>
      <span data-tip=${a.created_at}>${U(a.created_at)}</span>
      <${es} path=${t} />
      <${V} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${r} />
      <${Xe} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${Qs(a).map(([o,c])=>s`<tr><td class="muted">${o}</td><td>${c}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>L(S(t,{run:a.id}),{replace:!0})}>
            <${b} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${b} name="copy" size=${15} /> Copy the run id</button>
          ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
            <${b} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(o=>{let c=E("result",o.check);return s`<a class=${`check small tone-${c.tone}`} href=${S(o.group)} data-tip=${o.statement}>
              <${b} name=${c.icon} size=${14} />${o.group==="."?"own proposal":o.group}
              ${o.verdict?s`<${_} spec=${E("verdict",o.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function es({path:e}){let t=y(bt(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([o,c])=>`${ft(o)} ${F(c)}`).join(", "),a=te(e.split("/").pop()??""),r=`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}${n?` (${n})`:""}`;return s`<span data-tip=${r}>
    best <b>${t.label??ft(`metric.${t.metric}.${t.stat}`)} ${F(t.value)}</b>
    ${a?null:s` · <a href=${de(t.run)}>${t.name}</a>`}
  </span>`}function Qs(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var Et=80;function ts({node:e}){let t=J("main"),n=J(e.data?.keys?"keys":""),a=e.props.mode==="run",r=e.props.title??(a?"Config":"Hyperparameters");return s`<${ze} id=${`config:${e.id}`} title=${r} open=${e.props.open} result=${t}>
    ${t.data?a?s`<${Je} config=${t.data.config} varying=${Ae(n.data)} />`:s`<${ea} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function ea({rows:e}){let t=new Set(Ae({config:{rows:e}})),n=e.filter(([a])=>t.has(a.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([a,,r])=>{let o=Array.isArray(r)?r.map(F).join(", "):`${F(r.min)} \u2026 ${F(r.max)} \xB7 ${r.distinct} values`;return s`<tr><td data-tip=${a}>${a.replace(/^config\./,"")}</td>
      <td data-tip=${o.length>Et?o:void 0}>${o.length>Et?`${o.slice(0,Et-1)}\u2026`:o}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var ns=15e3;function ss({node:e}){let t=ce(Y),n=oe(),[a,r]=Wt(),o=e.props.code,c=y(r&&o?{method:"code",params:o,scope:null}:null),[i,l]=g(null),[u,m]=g(120),[p,v]=g({error:null,warnings:[]}),C=w=>{ue&&console.error(`[block ${e.id}] ${w}`),v(d=>({...d,error:w}))},x=I(()=>{});T(()=>{if(!i)return;let w=!0;Pe.n++;let d=()=>{w&&Pe.n--,w=!1};x.current=d;let $=setTimeout(()=>{w&&C(`no first render within ${ns/1e3} s`),d()},ns);return()=>{clearTimeout($),d()}},[i]),T(()=>{let w=i?.contentWindow;if(!w||c.status!=="ready")return;let d=N=>w.postMessage(N,"*"),$=new Map,h=new rn,H=N=>{if(N.source!==w)return;let k=N.data;switch(k.type){case"hello":d({type:"init",init:{id:e.id,code:c.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:Vt.value,pair:Ge.value,prefs:gt(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!nn.has(k.call.method)){d({type:"result",id:k.id,result:{status:"error",data:null,error:`${k.call.method} is not available in a custom block`,refreshing:!1}});break}$.get(k.id)?.(),$.set(k.id,It(k.call,re=>d({type:"result",id:k.id,result:re})));break;case"unsub":$.get(k.id)?.(),$.delete(k.id);break;case"navigate":k.url.startsWith("/")&&L(k.url);break;case"height":h.accept(performance.now())?m(Math.max(40,k.height)):B("its height keeps changing, so it is fixed at its last height");break;case"ready":v(re=>({...re,blank:k.blank,overflow:k.overflow})),x.current();break;case"warn":B(k.message);break;case"hover":mt.set(k.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(k.prefs)&&A.set(k.prefs);break;case"download":case"snapshot":k.href?sn(k.href,k.name)?performance.now()-j>1e3&&(j=performance.now(),Oe().download(k.href,k.name)):B(`a download of ${k.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":Oe().figure(k.spec,k.name).catch(re=>B(`the PDF failed: ${re.message}`));break;case"expand":an(k.node)&&Oe().expand(k.node,t);break;case"error":C(k.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,P)),x.current();break;default:break}},B=N=>{ue&&console.warn(`[block ${e.id}] ${N}`),v(k=>k.warnings.includes(N)?k:{...k,warnings:[...k.warnings,N]})},j=-1/0,A=gt(t.path),X=mt.subscribe(N=>d({type:"hover",run:N})),R=A.subscribe(N=>d({type:"prefs",prefs:N}));return addEventListener("message",H),d({type:"ping"}),()=>{X(),R(),removeEventListener("message",H);for(let N of $.values())N()}},[c.status,c.data?.code,i]),T(()=>{let w={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(w,"*")},[t.names,t.colors,t.metrics,i]),T(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let P=typeof o=="object"?o.path??o.block:String(o??"");qt(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let f=r&&c.status==="ready"&&!p.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${f?s`<span class="chart-tools">
            <${V} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${V} icon="x" label="Close (Esc)" onClick=${()=>Ie.set(null)} />`:s`<${V} icon="maximize" label="Expand" onClick=${()=>Oe().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${ne} caption=${e.props.expanded?void 0:e.props.caption} result=${c}>
      ${p.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${P})</span>
            <pre class="code">${p.error}</pre>
          </div>`:null}
      ${p.warnings.map(w=>s`<${O} kind="warning">${w}<//>`)}
      ${f?s`<div class="custom-frame" data-frame-blank=${p.blank?"1":void 0} data-frame-overflow=${p.overflow?"1":void 0}>
            <iframe key=${c.data.code} ref=${l} sandbox="allow-scripts" ...${ta()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function ta(){if(!!1)return{src:_t("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function as({node:e}){let t=J("main"),n=ce(Y),a=t.data?.entries??[];return s`<${ne} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${O}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Rt(_e(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${Re?"eager":"lazy"} />
          <figcaption class="small">step ${ye(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function rs({node:e}){let t=J("main"),n=t.data?.entries??[];return s`<${ne} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${O}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${ye(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function os({node:e}){let[t,n]=g(Re||e.props.open!==!1),a=s`${(e.children??[]).map(c=>s`<${ae} key=${c.id} node=${c} />`)}`,r=ce(qe);if(!e.props.title)return s`<div class="stack">${a}</div>`;let o=r===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${t} aria-label=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${()=>n(!t)}>
      <${b} name=${t?"chevron-down":"chevron-right"} size=${16} />${o?null:e.props.title}
    </button>
    ${t?s`<div class="stack">${a}</div>`:null}
  </div>`}function is({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${ae} key=${n.id} node=${n} />`)}
  </div>`}function ls({node:e}){let t=ce(Y),n=Ze(t.path),a=e.props.min_width??320,r=e.props.columns,o=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${a}px, 100%), 1fr))`,c=(e.children??[]).flatMap(m=>m.props.y??[]),i=e.props.addable?n.added.filter(m=>!c.includes(m)).map(m=>({block:"line",id:`added-${m}`,props:{y:m,added:!0},data:{main:{...e.props.template,params:{...e.props.template.params,y:[m]}}}})):[],l=tn([...e.children??[],...i],n.order[e.id]),u=(m,p)=>{let v=l.map(C=>C.id).filter(C=>C!==m);v.splice(v.indexOf(p),0,m),Qt(t.path,e.id,v)};return s`<div class="grid" style=${o}>
    ${l.map(m=>s`<${na} key=${m.id} node=${m} path=${t.path} span=${n.spans[m.id]??m.props.span??1}
      columns=${r} onDrop=${p=>p!==m.id&&u(p,m.id)} />`)}
    ${e.props.addable&&!!1?s`<${sa} path=${t.path} shown=${[...c,...n.added]} />`:null}
  </div>`}var Tt=[1,2,"full"];function na(e){let[t,n]=g(!1),a=Tt[(Tt.indexOf(e.span)+1)%Tt.length],r=o=>o==="full"?"full width":`${o} column${o===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${o=>{o.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${o=>{o.preventDefault(),n(!1),e.onDrop(o.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${o=>o.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${b} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(a)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>en(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ae} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function sa(e){let t=y({method:"keys",params:{from:e.path},scope:e.path}).data,n=(t?.metrics?.rows??[]).map(a=>a[0]).filter(a=>!e.shown.includes(a));return t&&!n.length?null:s`<div class="add-chart">
    <span class="add-chart-label"><${b} name="plus" size=${16} /> Add a chart</span>
    <${Ye} single options=${n} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([a])=>Qe(e.path,r=>({added:[...r.added,a]}))} />
  </div>`}function cs({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,r]=g(()=>t.find(i=>i.id===n())?.id??t[0]?.id),o=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},c=t.find(i=>i.id===a)??t[0];return Re?s`<div class="stack">${t.map(i=>s`<${ae} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===c?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>o(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${c?s`<div class="stack" role="tabpanel" id=${`panel-${c.id}`} aria-labelledby=${`tab-${c.id}`}>
          ${(c.children??[]).map(i=>s`<${ae} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var aa={section:os,row:is,grid:ls,line:pn,table:vn,stat:gn,images:as,text:rs,proposal:Fn,note:Jn,output:Xn,config:ts,memory:jn,groups:Gn,notes:Vn,tabs:cs,scatter:$n,bar:fn,histogram:hn,data_table:cn,timeline:dn,custom:ss,markdown:Yn};function ae({node:e}){return s`<${Jt} node=${e} blocks=${aa} />`}function ds(e,t){let n=e.split(`
`),a=t.split(`
`),r=n.length,o=a.length,c=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let m=r-1;m>=0;m--)for(let p=o-1;p>=0;p--)c[m][p]=n[m]===a[p]?c[m+1][p+1]+1:Math.max(c[m+1][p],c[m][p+1]);let i=[],l=0,u=0;for(;l<r&&u<o;)n[l]===a[u]?(i.push({kind:"same",text:n[l]}),l++,u++):c[l+1][u]>=c[l][u+1]?i.push({kind:"removed",text:n[l++]}):i.push({kind:"added",text:a[u++]});for(;l<r;)i.push({kind:"removed",text:n[l++]});for(;u<o;)i.push({kind:"added",text:a[u++]});return i}function us(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let r=a;for(;r<e.length&&e[r].kind==="same";)r++;let o=a===0?0:t,c=r===e.length?0:t;r-a>o+c+1?n.push(...e.slice(a,a+o),{kind:"skip",count:r-a-o-c},...e.slice(r-c,r)):n.push(...e.slice(a,r)),a=r}return n}var Mt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function ms(e){if(Mt[e.block])return Mt[e.block];if(e.block==="row"||e.block==="grid"){if(e.props.addable)return"charts";let n=new Set((e.children??[]).map(r=>Mt[r.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function ct(e){let t=y(He(e.path)),n=oe(),a=D(t.data),r=Le(()=>We(a.map(m=>m["run.id"]),n),[t.data,n]),o=Le(()=>new Map(a.map(m=>[m["run.id"],m["run.name"]??m["run.id"]])),[t.data]),c=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${c}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${z} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let i={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}},l=e.view.view;if(e.plain)return s`<div class=${c}><${Y.Provider} value=${i}><${ae} node=${l} /><//></div>`;let u=l.block==="section"&&!l.props.title?l.children??[]:[l];return s`<div class=${c}>${e.before}
    <${Y.Provider} value=${i}>
      ${u.map(m=>{let p=ms(m);return s`<${z} key=${m.id} label=${p}><${qe.Provider} value=${p}><${ae} node=${m} /><//><//>`})}
    <//>
  </div>`}function ps(e){if(null)return s`<div class="view-source small"><${b} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=M(W),a=n.page==="group"&&n.version,r=t.versions?s`<a href=${S(e.path,{history:!0})}><${b} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=s`draft <b>${t.draft}</b>`;break;case"view":o=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${U(he(t.version))} by ${t.author??"unknown"}`;break;default:o=s`the built-in view`}return s`<div class="view-source small">
    <${b} name="layout" size=${14} /><span>${o}</span>
    ${a?s`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!a?s`<${ra} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${oa} path=${e.path} />
        <${ia} path=${e.path} view=${t} />`}
  </div>`}function ra(e){let[t,n]=g(null),a=e.outdated.map(o=>o.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Cn(e.path)}catch(o){n(o.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${b} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function oa(e){let[t,n]=g(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Te.set(await tt(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${b} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function ia(e){let t=Ze(e.path),n=Zt(t),[a,r]=g(!1),[o,c]=g(e.view.title??""),[i,l]=g(e.view.finding??""),[u,m]=g(null),[p,v]=g(!1);if(!n&&!a)return null;let C=async x=>{x.preventDefault(),v(!0),m(null);try{let P={charts:t.charts,view:t.view,added:t.added,order:t.order,spans:t.spans};await K("save_view",{path:e.path,prefs:P,title:o,finding:i}),Qe(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),Se(f=>["view","view_history","summary"].includes(f.method)&&f.scope===e.path),r(!1)}catch(P){m(P.message)}finally{v(!1)}};return a?s`<form class="save-form" onSubmit=${C}>
    <${Be} label="Title"><input value=${o} onInput=${x=>c(x.target.value)} /><//>
    <${Be} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${x=>l(x.target.value)} /><//>
    <div class="save-actions">
      <${se} type="submit" icon=${p?"hourglass":"save"} disabled=${p}>${p?"Saving\u2026":"Save as view"}<//>
      <${se} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${u?s`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:s`<${se} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function $s(e){let t=y(_n(e.path)),n=t.data?.entries??[],[a,r]=g(null),o=a??n.slice(0,2).map(i=>i.version).reverse(),c=i=>{let l=o.includes(i)?o.filter(u=>u!==i):[...o,i].slice(-2);r(l.sort())};return t.status==="error"?s`<${O} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${b} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${O}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,l)=>s`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>c(i.version)} />
            <span class="num muted" data-tip=${i.version}>${U(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${l===0?S(e.path):S(e.path,{version:i.version})}
            onClick=${u=>{u.preventDefault(),L(l===0?S(e.path):S(e.path,{version:i.version}))}}>${l===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?s`<${la} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function la(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=y(t(e.a)).data,a=y(t(e.b)).data,r=y(pe(e.path,e.a)).data,o=y(pe(e.path,e.b)).data,c=n&&a?us(ds(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${U(he(e.a))} to ${U(he(e.b))}</h3>
    <pre class="diff code">${c.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${ct} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${o?.title??e.b}</h3><${ct} path=${e.path} view=${o} plain /></div>
    </div>
  </div>`}function fs(e){return Rn(e.path),e.history?s`<div class="page"><div class="sections">
      <${z} label=${hs(e.path)}><${Ct} path=${e.path} /><//>
      <${z} label="history"><${$s} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${ca} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function ca(e){let t=y(pe(e.path,e.version,e.draft));T(()=>{t.status==="ready"&&requestAnimationFrame(Ht)},[t.status==="ready"]);let n=s`
    <${z} label=${hs(e.path)}>
      <${Ct} path=${e.path} finding=${t.data?.finding} />
      ${t.data?s`<${ps} path=${e.path} view=${t.data} />`:null}
    <//>
    ${te(e.path.split("/").pop()??"")?null:s`<${Qn} path=${e.path} />`}`;return t.status==="error"?s`<div class="sections">${n}
      <${z} label="view">
        ${da(e.path,t.error)?s`<${O} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${O} kind="error">${t.error}<//>`}
      <//>
    </div>`:s`<${ct} path=${e.path} view=${t.data} before=${n} />`}function hs(e){return te(e.split("/").pop()??"")?"run":"group"}function da(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function gs(e){T(()=>{xe(pe(e.id)).then(n=>L(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=y(pe(e.id));return t.status==="error"?s`<div class="page"><${O} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var ua={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Nt=20,De=-1,ma=[["day",86400],["week",7*86400],["month",30*86400]];function bs(e){let t=D(y(ie()).data).map(i=>i.path),n=y({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=y({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Ue("Timeline",D(n.data).filter(i=>i["run.status"]==="running").length);let r=Date.now()/1e3,o=D(n.data).filter(i=>i["run.created_at"]).map((i,l)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:l})),c=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(he(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${z} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Be} label="Group" inline>
          <select value=${e.from} onChange=${i=>L(je(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${o.length} runs · ${c.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${z} label="runs">
      ${n.status==="error"?s`<${O} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${pa} bars=${o} marks=${c} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function pa(e){let t=oe(),n=I(null),a=[...e.bars.flatMap(f=>[f.start,f.end]),...e.marks.map(f=>f.t)],r=a.length?vs(Math.min(...a),Math.max(...a)):vs(Date.now()/1e3-86400,Date.now()/1e3),[o,c]=g(r),i=e.bars.length,l=Math.min(900,Math.max(160,(i+1.5)*Nt+40)),m=un(n,mn,t?(f=>{let w=on(o[0],o[1]),d=h=>f.colors[ua[h]??"muted"],$=h=>f.colors[h==="verdict"?"good":h==="decision"?"accent":h==="question"?"warn":"muted"];return{style:Gt(f),height:l,x:{range:o,log:!1,format:h=>ln(h,w.step),label:"",splits:w.at},y:{range:[De-.8,i+.5],log:!1,reverse:!0,label:"",size:150,splits:i<=40?[De,...e.bars.map(h=>h.lane)]:[De],format:h=>h===De?"notes":va(e.bars[Math.round(h)]?.name??"")},draw:({ctx:h,x:H,y:B,px:j,focused:A})=>{let X=Nt*.62*j;for(let R of e.bars){let N=H(R.start),k=Math.max(3*j,H(R.end)-N);h.fillStyle=A!==null&&A!==R.id?jt(d(R.status),.35):d(R.status),h.beginPath(),h.roundRect(N,B(R.lane)-X/2,k,X,3*j),h.fill()}for(let R of e.marks){let N=H(R.t),k=B(De),re=(A===R.id?6:4.5)*j;h.fillStyle=$(R.type),h.beginPath(),h.moveTo(N,k-re),h.lineTo(N+re,k),h.lineTo(N,k+re),h.lineTo(N-re,k),h.closePath(),h.fill()}},hit:(h,H,B,j)=>{if(Math.abs(H-j(De))<Nt/2){let R=ga(e.marks,N=>Math.abs(B(N.t)-h),8);return R?{key:R.id,rows:fa(R)}:null}let A=Math.round((H-j(0))/(j(1)-j(0))),X=e.bars.find(R=>R.lane===A&&B(R.start)-3<=h&&h<=Math.max(B(R.end),B(R.start)+3)+3);return X?{key:X.id,rows:$a(X)}:null},onClick:h=>{let H=e.marks.find(B=>B.id===h);H?L(S(H.group,{drawer:!0})):L(de(h))}}})(t):null,[o,e.bars,e.marks],t),p=f=>{if(!m.current)return;f.preventDefault();let w=m.current.xAt(f.clientX),d=Math.exp(f.deltaY*.0015);c(([$,h])=>Dt([w-(w-$)*d,w+(h-w)*d],r))},v=I(null),C=f=>v.current={x:f.clientX,range:o},x=f=>{if(!v.current||!m.current||!(f.buttons&1))return;let w=(f.clientX-v.current.x)*m.current.xPerPixel(),[d,$]=v.current.range;Math.abs(f.clientX-v.current.x)>3&&c(Dt([d-w,$-w],r))},P=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${ma.map(([f,w])=>s`<button type="button" role="radio" aria-checked=${Math.abs(o[1]-o[0]-w)<1}
          onClick=${()=>c(Dt([P-w,P+w*.02],[Math.min(r[0],P-w),r[1]]))}>last ${f}</button>`)}
      <button type="button" role="radio" aria-checked=${o[0]===r[0]&&o[1]===r[1]} onClick=${()=>c(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${l}px`}
      onWheel=${p} onPointerDown=${C} onPointerMove=${x} onPointerUp=${()=>v.current=null}></div>
    <p class="muted small">${ha(t)}</p>
  </div>`}function $a(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:U(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Ce(e.end-e.start),color:null}]}function fa(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:U(new Date(e.t*1e3).toISOString()),color:null}]}function ha(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function ga(e,t,n){let a=null,r=n;for(let o of e){let c=t(o);c<r&&([a,r]=[o,c])}return a}function vs(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Dt([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-a));return[r,r+a]}function va(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function ys(){let e=M(Ie),t=I(null);if(T(()=>{let r=t.current;if(!r||!e)return;r.showModal();let o=()=>Ie.set(null);return r.addEventListener("close",o),()=>r.removeEventListener("close",o)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${Y.Provider} value=${e.view}><${ae} node=${n} /><//>
  </dialog>`}function ws(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let r=a.indexOf(n);if(r>=0)return 100-Math.min(r,50)-a.length/100;let o=0,c=0;for(let i of a)if(i===n[o]?o++:o>0&&c++,o===n.length)return 40-Math.min(c,39);return 0}function xs(e){let[t,n]=g(e.query),[a,r]=g(0),o=I(null),c=D(y(ie()).data),i=D(y(st()).data);T(()=>{let d=o.current;d.showModal();let $=()=>Q.set(null);d.addEventListener("close",$);let h=!1,H=A=>{let X=d.getBoundingClientRect();return A.clientX<X.left||A.clientX>X.right||A.clientY<X.top||A.clientY>X.bottom},B=A=>h=H(A),j=A=>h&&H(A)&&d.close();return"closedBy"in HTMLDialogElement.prototype||(d.addEventListener("pointerdown",B),d.addEventListener("pointerup",j)),()=>{d.removeEventListener("close",$),d.removeEventListener("pointerdown",B),d.removeEventListener("pointerup",j)}},[]);let l=()=>o.current?.close(),u=d=>()=>L(d),m=W.value,p=m.page==="group"?m.path:".",v=(d,$,h,H)=>({section:"Commands",label:d,detail:$,sym:{icon:h,tone:"muted",label:d},run:H}),x=[...c.map(d=>({section:"Groups",label:d.path==="."?"local":d.path,detail:`${d.runs} runs${d.proposal?` \xB7 ${d.proposal}`:""}`,sym:E("research",d.status),run:u(S(d.path))})),...i.map(d=>({section:"Runs",label:d["run.name"]??d["run.id"],detail:`${d["run.status"]} \xB7 ${d["run.path"]}`,sym:E("run",d["run.status"]),run:u(S(d["run.path"]))})),v("Theme: light","","sun",()=>Ve("light")),v("Theme: dark","","moon",()=>Ve("dark")),v("Theme: follow the system","","monitor",()=>Ve("system")),v("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),v("Show notes and timeline","i","file-text",u(S(p,{drawer:!0}))),v("Show or hide the sidebar","\u2318B","panel-left",()=>Z.set(!Z.value)),v(ee.value?"Resume live updates":"Pause live updates","p",ee.value?"play":"pause",()=>ee.set(!ee.value)),v("Keyboard shortcuts","?","keyboard",()=>$e.set(!0)),v("Settings","","settings",u("/settings/appearance"))].map(d=>({it:d,s:Math.max(ws(t,d.label),ws(t,d.detail)*.5)})).filter(d=>d.s>0).sort((d,$)=>$.s-d.s||ks(d.it.section)-ks($.it.section)).slice(0,60).map(d=>d.it),P=d=>{d&&(l(),d.run())},f=d=>{if(d.key==="ArrowDown")r(Math.min(x.length-1,a+1));else if(d.key==="ArrowUp")r(Math.max(0,a-1));else if(d.key==="Enter")P(x[a]);else return;d.preventDefault()},w="";return s`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${b} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${x[a]?`pal-${a}`:void 0}
        onInput=${d=>{n(d.target.value),r(0)}} onKeyDown=${f} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${x.map((d,$)=>{let h=d.section!==w&&!t?w=d.section:null;return s`${h?s`<li class="palette-head small" role="presentation">${h}</li>`:null}
          <li id=${`pal-${$}`} class="item" role="option" aria-selected=${$===a}
              onMouseMove=${()=>r($)} onClick=${()=>P(d)}>
            <${_} spec=${d.sym} /><span class="label">${d.label}</span><span class="detail small">${d.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function ks(e){return["Groups","Runs","Commands"].indexOf(e)}function dt(e,t=[]){let n=new Map,a=(i,l={})=>({path:i,name:i==="."?"local":i.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let i of e)n.set(i.path,a(i.path,i));(t.length===0||t.some(i=>i.name==="local"))&&!n.has(".")&&n.set(".",a("."));for(let i of t){let l=i.name==="local"?".":i.name;n.has(l)||n.set(l,a(l)),Object.assign(n.get(l),{state:i.state,error:i.error})}for(let i of n.values()){if(G(i.path))continue;let l=i.path.lastIndexOf("/"),u=l<0?".":i.path.slice(0,l);(n.get(u)??n.get(be(i.path))??n.get(".")).children.push(i)}for(let i of n.values())i.children.sort((l,u)=>l.name.localeCompare(u.name));let o=[...n.values()].filter(i=>i.path!=="."&&G(i.path)).sort((i,l)=>i.name.localeCompare(l.name)),c=n.get(".");return c?[c,...o]:o}function Ss(e,t,n,a=new Set){let r=[],o=n.toLowerCase(),c=i=>{(!o||i.path.toLowerCase().includes(o)||Cs(i,o))&&(r.push(i),(o||(G(i.path)?!a.has(i.path):t.has(i.path)))&&i.children.forEach(c))};return e.forEach(c),r}function Cs(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Cs(n,t))}function Es(e,t){if(G(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),r=o=>o.path===a?o:o.children.map(r).find(c=>c)??null;return e.map(r).find(o=>o)?.children??[]}function Ts(e){return G(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Ms(){let e=M(W),t=y(ie()),[n,a]=g(()=>new Set(we("open",[]))),[r,o]=g(()=>new Set(we("closed-hosts",[]))),[c,i]=g(""),l=I(null),u=e.page==="group"?e.path:null,m=dt(D(t.data),t.data?.meta?.sources??[]),p=Ss(m,wa(n,u),c,r),v=f=>G(f)?!r.has(f):n.has(f),C=(f,w)=>{let d=w??!v(f);if(G(f)){let h=new Set(r);d?h.delete(f):h.add(f),ke("closed-hosts",[...h]),o(h);return}let $=new Set(n);d?$.add(f):$.delete(f),ke("open",[...$]),a($)},x=I(u);return T(()=>{u!==x.current&&u&&!G(u)&&r.has(be(u))&&C(be(u),!0),x.current=u},[u]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${b} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${c} aria-label="Filter groups"
        onInput=${f=>i(f.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${f=>{let w=[...l.current?.querySelectorAll("a.tree-item")??[]],d=w.indexOf(document.activeElement),$=p[d];switch(f.key){case"ArrowDown":w[Math.min(w.length-1,d+1)]?.focus();break;case"ArrowUp":w[Math.max(0,d-1)]?.focus();break;case"ArrowRight":$?.children.length&&C($.path,!0);break;case"ArrowLeft":$?.children.length&&v($.path)?C($.path,!1):$&&w[p.findIndex(h=>h.path===ya($.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${p.map(f=>s`<${ba} key=${f.path} node=${f} current=${f.path===u}
        open=${v(f.path)||!!c} onToggle=${()=>C(f.path)} />`)}
    </div>
  </nav>`}function ba(e){let t=e.node,n=()=>Ke(t.path),a=t.children.length>0,r=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${G(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${8+Ts(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${o=>{o.metaKey||o.ctrlKey||(o.preventDefault(),L(S(t.path)))}}>
    <span class="twisty" onClick=${o=>{o.preventDefault(),o.stopPropagation(),e.onToggle()}}>
      ${a?s`<${b} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${G(t.path)?s`<${_} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${_} spec=${E("run","running")} size=${14} />`:null}
      ${t.failed?s`<${_} spec=${{...E("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function ya(e){if(G(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function wa(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let r=1;r<a.length;r++)n.add(a.slice(0,r).join("/"));return n}function Ds(){let e=M(W),t=M(Z),n=M(Q),a=M($e),r=I(null);T(()=>At(()=>r.current),[]),T(()=>(addEventListener("keydown",Ns),()=>removeEventListener("keydown",Ns)),[]);let o=e.page==="group"&&e.drawer,c;switch(e.page){case"group":c=s`<${fs} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":c=s`<${gs} id=${e.id} />`;break;case"settings":c=s`<${Bn} />`;break;case"timeline":c=s`<${bs} key=${e.from} from=${e.from} />`;break;default:c=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return ue||!1?s`<main class="main render-main" ref=${r}>${c}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${Hn} />
    ${t?s`<${Ms} />`:null}
    <main class="main" ref=${r}>${c}</main>
    ${o?s`<${Zn} path=${e.path} run=${e.run} />`:null}
    <${Kn} />
    ${n!==null?s`<${xs} query=${n} />`:null}
    ${a?s`<${xa} />`:null}
    <${ys} />
  </div>`}function Ns(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),Q.set(Q.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Z.set(!Z.value);return}if(e.key==="Escape"){if(Q.value!==null||$e.value)return;let a=W.value;return a.page==="group"&&a.run?L(S(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?L(S(a.path),{replace:!0}):void 0}if(t||e.altKey||On(e)||Q.value!==null||$e.value)return;let n=W.value;switch(e.key){case"/":e.preventDefault(),Q.set("");break;case"?":$e.set(!$e.value);break;case"p":ee.set(!ee.value);break;case"i":n.page==="group"&&L(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Z.set(!Z.value);break;case"[":case"]":n.page==="group"&&ka(n.path,e.key==="]"?1:-1);break}}async function ka(e,t){let n=await xe(ie()),a=Es(dt(D(n),n?.meta?.sources??[]),e),r=a.findIndex(c=>c.path===e),o=a[r+t];o&&L(S(o.path))}function xa(){let e=I(null);return T(()=>{let t=e.current;t.showModal();let n=()=>$e.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${rt.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${se} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Kt();if(ue){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(me.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Pe.n,Ut&&Xt()}bn();var Sa=K("meta").then(e=>(ue&&(e={...e,settings:{...e.settings,theme_mode:me.value}}),ot(e),e));!ue&&!!1&&Bt(async()=>{let[e,t]=await Promise.all([Sa,K("meta")]);e.bundle!==t.bundle?location.reload():ot(t)});Lt(s`<${Ds} />`,document.getElementById("app"));
