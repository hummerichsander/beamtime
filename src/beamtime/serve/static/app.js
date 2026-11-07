import{$ as Ae,A as Xt,Aa as wt,B as me,Ba as $n,C as Ie,D as Yt,E as Xe,Ea as fn,F as ht,Fa as hn,G as pe,Ga as gn,H as en,Ha as yn,I as gt,Ia as wn,J as Ye,Ja as kn,K as U,L as J,M as le,N as Je,O as tn,Oa as xn,Q as ze,Qa as Cn,R as Be,Ra as Sn,Sa as En,T as nn,Ta as Tn,U as sn,Ua as Mn,V as k,Va as Nn,W as I,Wa as Dn,X as Ze,Y as ae,Z as z,_ as P,a,aa as V,ba as an,ca as O,d as K,da as re,e as Le,ea as He,f as Se,fa as vt,g as ft,ga as Qe,h as x,ha as et,i as Ft,ia as rn,j as ne,ja as Ke,k as jt,ka as te,l as Gt,la as tt,m as Vt,n as Ee,o as se,oa as on,p as S,pa as ln,q as qe,qa as Ue,r as ue,ra as cn,s as _e,sa as dn,t as ke,ta as un,u as G,ua as M,v as W,va as yt,w as Wt,wa as mn,xa as pn,y as R,ya as Fe,z as qt,za as nt}from"./chunks/chunk-FV3TDTMD.js";import{a as Kt,b as Ut}from"./chunks/chunk-O2K4N3UR.js";import{B as Zt,C as Qt,D as oe,G as be,H as xe,I as Ce,J as F,K as bt,V as vn,W as bn,b as Bt,d as At,f as y,g as T,h as Ht,i as L,j as Re,k as Y,n as we,o as N,p as ge,q as ve,v as Jt,x as Oe}from"./chunks/chunk-VBF3SWAC.js";import"./chunks/chunk-VC46IEJQ.js";function Te(e,t){Ee(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var kt=["notes","timeline","groups","check","card","memory_show","status"];async function st(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Te(e.group,kt)}async function Pn(e,t,n,s){await K("note_add",{group:e,type:t,description:n,body:s}),Te(e,kt)}async function Rn(e,t){await K("memory_update",{group:e,body:t}),Te(e,["memory_show","status"])}async function Ln(e,t){let n=await K("proposal_show",{group:e}),s=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await K("proposal_set",{group:e,proposal:{...s,statement:t}}),Te(e,["groups","proposal_show","check","summary"])}async function _n(e){await K("note_rm",{note:e.id}),Te(e.group,kt)}async function In(e,t,n){await K("name",{run:e,name:n}),Te(t,["card","runs","groups","summary","series"])}async function at(e,t,n){let s=await K("view_text",{path:e,id:t,text:n});return Ee(r=>["view","view_history"].includes(r.method)&&r.scope===e),s.id}async function On(e){await K("view_upgrade",{group:e}),Ee(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Me=new we(null);async function zn(e,t){return await K("set",{key:e,value:t}),K("meta")}var ce=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),$e=(e,t=null,n=null,s=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...s?{metrics:s}:{}},scope:e}),xt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),Ne=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Bn=e=>({method:"check",params:{group:e},scope:e}),An=e=>({method:"proposal_show",params:{group:e},scope:e}),De=(e,t)=>({method:"card",params:{run:_e(e,t)},scope:t}),Hn=(e,t)=>({method:"output",params:{run:_e(e,t),tail:30},scope:t}),je=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),rt=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Kn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Un=()=>({method:"status",params:{},scope:"."}),ot=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ge(e){let t=Ke(e).value.main;for(let n of[$e(e,null,null,t),Ne(e),je(e),xt(e,t)])ft(n);Se($e(e,null,null,t)).then(n=>{for(let s of Fn(n.view))ft(s)}).catch(()=>{})}function Fn(e){return e?[...Fs.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(Fn)]:[]}var Fs=new Set(["line","custom"]),jn=e=>({method:"view_history",params:{group:e},scope:e});var Ct="/static/favicon.svg",it=null;async function js(){if(it)return it;let e=new Image;e.src=Ct,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let s=n.getContext("2d");if(!s)return Ct;s.drawImage(e,0,0,t,t),s.beginPath(),s.arc(t-6,t-6,6,0,Math.PI*2);let r=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return s.fillStyle=r||"#2f5aa8",s.fill(),it=n.toDataURL("image/png"),it}function Gs(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=Ct;return}js().then(n=>{t.type="image/png",t.href=n})}}function Ve(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,Gs(t>0)},[e,t])}function Gn(e){let t=se(e.split("/").pop()??""),n=x(t?null:Ne(e)),s=x(t?De(e.split("/").pop()??"",e):null),r=t?s.data?.run.name??s.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,i=t?s.data?.run.status==="running"?1:0:P(n.data)[0]?.running??0;Ve(r,i)}var Z=new we(ge("sidebar",!0)),Q=new we(null),fe=new we(!1),he=new we(null);Z.subscribe(e=>ve("sidebar",e));var Vn=ge("visit",Date.now());ve("visit",Date.now());function Wn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var lt=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Vs=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function ct(e){he.set(e),Xe.set(e.theme),Oe.set(e.colormaps),e.settings?.theme_mode&&pe.set(e.settings.theme_mode),gt()}var qn=0;async function St(e,t){let n=++qn;e==="theme_mode"&&(pe.set(t),gt());let s=await zn(e,t);n===qn&&ct(s)}function Xn(){let e=N(pe),t=le(),n=N(he),[s,r]=y(null);Ve("Settings");let i=(l,d)=>{r(null),St(l,d).catch(v=>r(v.message))},c=n?.settings??{},o=(l,d,v)=>a`
    <label class="field-label small" for=${`setting-${l}`}>${d}</label>
    <span class="input body">
      <select id=${`setting-${l}`} value=${c[l]} onChange=${u=>i(l,u.target.value)}>
        ${v.map(u=>a`<option value=${u}>${u}</option>`)}
      </select>
    </span>`;return a`<div class="page settings"><div class="sections">
    <${O} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${c.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${s?a`<${z} kind="error">${s}<//>`:null}
    <//>
    <${O} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Vs.map(([l,d,v])=>a`<button type="button" role="radio" aria-checked=${e===l} onClick=${()=>i("theme_mode",l)}>
            <${k} name=${d} size=${15} />${v}</button>`)}
        </div>
        ${o("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(l=>a`<${z} kind="warning">${l}<//>`)}
    <//>
    <${O} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?a`<${et} options=${n.figure_styles} value=${c.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${l=>i("figure_style",l)} />`:a`<span class="muted small"><code>${JSON.stringify(c.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(c.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${O} label="keyboard">
      <table class="kv">${lt.map(([l,d])=>a`<tr><td><kbd class="small">${l}</kbd></td><td>${d}</td></tr>`)}</table>
    <//>
    <${O} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(l=>a`
          <tr><td class="muted">${l.name}</td><td><code class="code">${l.logdir}</code> (${l.kind}, ${l.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var Yn={system:"light",light:"dark",dark:"system"},Ws={system:"monitor",light:"sun",dark:"moon"};function Jn(){let e=N(he),t=N(pe),n=N(Z);return a`<header class="topbar">
    <${V} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Z.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>Q.set("")} aria-label="Search (⌘K)">
      <${k} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${qs} />
      <${V} icon=${Ws[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${Yn[t]})`}
        onClick=${()=>{St("theme_mode",Yn[t])}} />
      <a class="icon-button" href=${qe(W.value.page==="group"?W.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${k} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${k} name="settings" size=${16} /></a>
    </div>
  </header>`}function qs(){let t=(x(ce()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?a`${[{name:"local",state:"connected"},...t].map(n=>a`<a class=${`source small ${n.state}`}
      href=${S(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${k} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:a`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${k} name="server" size=${15} /> local</span>`}function Xs(e){let[t,n]=y(Date.now());return T(()=>{let s=setInterval(()=>n(Date.now()),e);return()=>clearInterval(s)},[e]),t}function Ys(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function Zn(){let e=N(jt),t=N(ne),n=N(Gt),s=N(W),r=Xs(5e3),i=x(Un()).data,c=P(x(ot()).data),o=N(he),l=i?.daemon,d=i?.runs?.running??0,v=c.filter(E=>E["run.status"]==="failed"&&Ys(E["run.ended_at"])>Vn).length,u=i?.meta?.freshness,[p,h,g]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&l?["",`live \xB7 updated ${F(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${l.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return a`<footer class="statusbar small">
    <span class="status-item" data-tip=${g}><span class=${`live-dot ${p}`}></span>${h}</span>
    ${d?a`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>Q.set("running")}>
          <${k} name="circle-dot" size=${14} class="tone-accent" />${d} running</button>`:null}
    ${v?a`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>Q.set("failed")}>
          <${k} name="circle-x" size=${14} />${v} failed since your last visit</button>`:null}
    ${u?.behind?a`<span class="status-item warn-text" data-tip=${u.text}><${k} name="hourglass" size=${14} />${u.behind} runs behind</span>`:null}
    ${u?.damaged?.length?a`<span class="status-item warn-text" data-tip=${u.damaged.join(`
`)}><${k} name="triangle-alert" size=${14} />${u.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${s.page==="group"&&s.run?a`<span class="status-item"><${k} name="activity" size=${14} />1 run selected</span>`:null}
    <${V} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ne.set(!t)} />
    ${o?.outdated?a`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${o?.version?`beamtime ${o.version}`:""}</span>
  </footer>`}var Qn=null;function dt(e){let t=L(null),[n,s]=y(null),[r,i]=y(!1),[c,o]=y(!1);T(()=>{let u=!0;return Qn??=import("./chunks/md-SW3VT2BQ.js"),Qn.then(p=>p.render(e.text??"")).then(p=>u&&s(p)),()=>{u=!1}},[e.text]),Ht(()=>{let u=t.current;if(!u||!e.clamp)return;let p=()=>o(u.scrollHeight>u.clientHeight+2),h=new ResizeObserver(p);return h.observe(u),()=>h.disconnect()},[e.clamp,n]);let l=e.clamp&&!r,d=`md${l?" clamped":""}`,v=l?`--clamp:${e.clamp}`:"";return a`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?a`<div class=${d} ref=${t} style=${v}>
          ${(e.text??"").split(/\n{2,}/).map(u=>a`<p>${u}</p>`)}
        </div>`:a`<div class=${d} ref=${t} style=${v} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(c||r)?a`<button type="button" class="link small more" onClick=${()=>i(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function ye(e){let[t,n]=y(!!e.startEditing),[s,r]=y(e.value),[i,c]=y(null),[o,l]=y(null),d=L(null),v=L(!1);T(()=>c(null),[e.value]),T(()=>{!t||!d.current||(d.current.focus(),e.startEditing?d.current.select():d.current.setSelectionRange(d.current.value.length,d.current.value.length))},[t]);let[u,p]=y(!1),h=e.locked??void 0,g=$=>{if(!$.target.closest("a, button, input, summary")){if(h)return p(!0);$.preventDefault(),r(i??e.value),l(null),v.current=!1,n(!0)}},E=()=>{v.current=!0,n(!1),l(null),e.onCancel?.()},f=async()=>{if(v.current)return;v.current=!0;let $=e.multiline?s.trim():s.replace(/\s*\n\s*/g," ").trim();if($===e.value.trim()||!$&&!e.multiline)return E();n(!1),c($);try{await e.onSave($)}catch(b){c(null),r($),l(b.message),v.current=!1,n(!0)}},w=$=>{if($.key==="Escape")return $.preventDefault(),$.stopPropagation(),E();$.key!=="Enter"||$.isComposing||$.keyCode===229||(!e.multiline||$.metaKey||$.ctrlKey)&&($.preventDefault(),f())};if(t)return a`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${d} class="edit-field" value=${s} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,s.split(`
`).length+1)):1}
        onInput=${$=>r($.target.value)} onKeyDown=${w} onBlur=${f}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${o?a` · <span class="bad-text">${o}</span>`:null}</span>
    </div>`;let m=i??e.value;return a`<div class=${`editable${h?" locked":""}${i!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${h?`${e.label}: ${h}`:`Edit ${e.label}`}
      data-tip=${h} onClick=${g} onBlur=${()=>p(!1)}
      onKeyDown=${$=>$.key==="Enter"&&$.target===$.currentTarget&&g($)}>
    ${m.trim()?e.render?e.render(m):m:a`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${u&&h?a`<span class="edit-hint small locked-why" role="status"><${k} name="lock" size=${14} /> ${h}</span>`:null}
  </div>`}function Et(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function es({node:e}){let t=J("proposal"),n=J("check"),s=t.data,r=n.data;if(!s)return a`<${ae} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let i=s.proposal??{},c=(s.versions??[]).filter(l=>l.version!==s.version),o=!e.props.of||e.props.of===".";return a`<${ae} title="Predictions" result=${t} class="proposal">
    ${o?null:a`<p class="statement">${i.statement}</p>`}
    ${i.rationale?a`<p class="rationale prose">${i.rationale}</p>`:null}
    <${pn} predictions=${r?.predictions} />
    ${c.length?a`<${vt} summary=${`${c.length} earlier version${c.length>1?"s":""}`}>
          ${c.map(l=>a`<p class="small"><code>${l.version}</code> ${l.statement}
            <span class="muted">(${l.runs} runs, check ${l.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function ts({node:e}){let t=J("main"),n=e.data?.main.params.group??".",s=t.data?.chain??[],r=s.find(o=>o.group===n)??null,i=s.filter(o=>o.group!==n),c=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return a`<${Ae} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?c:void 0} open=${!1} result=${t}
      action=${a`<${I} spec=${{icon:"circle-help",tone:"muted",label:Zs}} />`}>
    <${ye} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${o=>a`<${dt} text=${o} />`} onSave=${o=>Rn(n,o)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=Js)?a`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?a`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?a` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${i.length?a`<p class="memory-meta small">Memory above this group: ${i.map((o,l)=>a`${l?", ":""}<a href=${S(o.group)}>${o.group==="."?"local":o.group}</a>`)}</p>`:null}
  <//>`}var Js=5,Zs="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Qs="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function ns({node:e}){let t=J("main"),n=e.data?.main.params.from??".",s=P(t.data).filter(r=>r.path!==n);return a`<${ae} title=${e.props.title} count=${t.data?String(s.length):void 0} result=${t}>
    ${t.data&&!s.length?a`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${s.map(r=>{let[i,c]=Et(r.progress),o=(r.failed??0)+(r.killed??0)+(r.lost??0);return a`<a class="group-row" key=${r.path} href=${S(r.path)}
            onPointerEnter=${()=>Ge(r.path)} onFocus=${()=>Ge(r.path)}>
          <${I} spec=${M("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?a`<span class=${`tone-${M("research",r.status).tone}`}>${M("research",r.status).label}</span>`:null}
            ${r.check?a`<${I} spec=${M("result",r.check)} word />`:null}
            ${r.verdict?a`<${I} spec=${M("verdict",r.verdict)} />`:null}
            ${i?a`<span data-tip=${c}>${i}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?a`<${I} spec=${M("run","running")} />`:null}
            ${o?a`<span class="tone-bad num" data-tip="failed, killed or lost"><${k} name="circle-x" size=${14} /> ${o}</span>`:null}
          </span>
          ${r.proposal?a`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function ss({node:e}){let t=J("main"),n=e.data?.main.params.from??".",[s,r]=y(!1),i=(t.data?.entries??[]).filter(o=>!String(o.state??"").startsWith("superseded")),c=t.data?.meta?.matched??i.length;return a`<${Ae} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(c):void 0} result=${t}
      action=${a`<${I} spec=${{icon:"circle-help",tone:"muted",label:Qs}} />
        ${a`<${V} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${s?a`<${na} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!i.length&&!s?a`<p class="muted small">No notes yet.</p>`:null}
      ${i.map(o=>a`<${ut} key=${o.id} note=${o} scope=${n} />`)}
      ${t.data?.more&&e.data?a`<${as} call=${e.data.main} before=${i[i.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var ea=20;function as(e){let[t,n]=y(!1),s=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:ea}}:null,r=x(s);if(!t)return a`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return a`<p class="bad-text small">${r.error}</p>`;let i=r.data?.entries??[];return a`${r.data?null:a`<div class="skeleton" style="block-size: 40px"></div>`}
    ${i.map(c=>a`<${ut} key=${c.id} note=${c} scope=${e.scope} />`)}
    ${r.data?.more?a`<${as} call=${e.call} before=${i[i.length-1]?.id} scope=${e.scope} />`:null}`}var ta=["observation","decision","idea","question","theory"];function rs(e){return(e?.note_types??ta).filter(t=>t!=="verdict")}function na(e){let t=rs(N(he)),[n,s]=y("observation"),[r,i]=y(""),[c,o]=y(""),[l,d]=y(null),[v,u]=y(!1),p=async g=>{if(g.preventDefault(),!r.trim())return d("give the note a title");u(!0);try{await Pn(e.group,n,r.trim(),c.trim()),e.onDone()}catch(E){d(E.message),u(!1)}};return a`<form class="note new-note" onSubmit=${p} onKeyDown=${g=>{g.key==="Escape"&&e.onDone(),g.key==="Enter"&&(g.metaKey||g.ctrlKey)&&p(g)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${g=>s(g.target.value)}>
        ${t.map(g=>a`<option value=${g}>${g}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${r} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${g=>i(g.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${c} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${g=>o(g.target.value)}></textarea></span>
    <div class="save-actions">
      <${re} type="submit" icon=${v?"hourglass":"plus"} disabled=${v}>${v?"Adding\u2026":"Add note"}<//>
      <${re} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${l?a`<span class="bad-text small">${l}</span>`:null}
    </div>
  </form>`}function sa({note:e}){let t=rs(N(he)).filter(n=>n!==e.type);return e.type==="verdict"?a`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${k} name=${M("note","verdict").icon} size=${15} /></span>`:a`<${Qe} icon=${M("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>a`<button type="button" key=${n} onClick=${()=>st(e,{type:n})}>
        <${k} name=${M("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function ut(e){let t=e.note,[n,s]=y(!!e.open),[r,i]=y(!1),c=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,o=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),l=t.meta?.author;return a`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${d=>!d.target.closest(".editable, a, .note-delete, .popover-wrap")&&s(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${k} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${sa} note=${t} />
      <${ye} value=${t.description} label="the note's title" class="note-title heading" render=${ra}
        onSave=${d=>st(t,{description:d})} />
      ${t.overall?a`<${I} spec=${M("verdict",t.overall)} />`:null}
      ${t.state?a`<${an} tone="warn">${t.state}<//>`:null}
      ${c?a`<a class="note-group small" href=${S(c)} data-tip="from this group">${aa(c,e.scope)}</a>`:null}
      <span class="note-meta small">${l?`${l} \xB7 `:""}${F(o)}</span>
      ${a`<${V} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${d=>{d.stopPropagation(),i(!r)}} />`}
    </div>
    ${r?a`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${re} icon="trash" kind="danger" onClick=${()=>{_n(t)}}>Delete<//>
          <${re} icon="x" kind="quiet" onClick=${()=>i(!1)}>Cancel<//>
        </div>`:null}
    ${n?a`<${ye} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${d=>a`<${dt} text=${d} />`}
          onSave=${d=>st(t,{body:d})} />`:null}
  </article>`}function aa(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,s=n.split("/").pop()??n;return se(s)?s.slice(-8):n}function os({node:e}){let t=J("main"),n=t.data?.lines??[],s=t.data?.meta??{},r=a`<${k} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${s.total_lines??n.length} lines${(s.shown??0)<(s.total_lines??0)?`, last ${s.shown}`:""}`:""}</span>`;return a`<${ae} result=${t}>
    <${vt} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function is({node:e}){let t=Y(U);return a`<${ae} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ye} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Me.value===e.id} onCancel=${()=>Me.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>a`<${dt} text=${n} />`}
      onSave=${n=>(Me.set(null),at(t.path,e.id,n))} />
  <//>`}function ls({node:e}){return a`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function ra(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let s=n.slice(2,-2),[r]=s.split(/[#@]/),i=r.split("/").pop()??"";return a`<a href=${se(i)?ue(i):S(r)}>${s}</a>`}return n.startsWith("`")?a`<code>${n.slice(1,-1)}</code>`:n})}function cs(e){let t=()=>R(S(e.path),{replace:!0});return a`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${k} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${V} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?a`<${oa} id=${e.run} scope=${e.path} />`:a`<${ia} path=${e.path} />`}
  </aside>`}function oa({id:e,scope:t}){let n=x(De(e,t)).data,s=x(Hn(e,t)).data,r=x(je(t)).data,i=x({method:"keys",params:{from:t},scope:t}).data,c=le(),o=Re(()=>Je(P(r).map(u=>u["run.id"]),c).get(e),[r,c,e]);if(!n)return a`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let l=n.run,d=Object.entries(n.metrics??{}),v=Jt(o,c);return a`<div class="drawer-body">
    <h3 class="heading"><span class=${v.class} style=${v.style}></span>
      <a href=${ue(e)}>${l.name}</a></h3>
    <p class="facts small">
      <${I} spec=${M("run",l.status)} word />
      <span><b>${xe(l.steps)}</b> steps</span>
      <span><b>${Ce(l.duration_s)}</b></span>
      <span data-tip=${l.created_at}>${F(l.created_at)}</span>
    </p>
    ${l.error?a`<pre class="log code bad-text">${l.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <${nt} config=${n.config??{}} varying=${Fe(i)} />
    ${d.length?a`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${d.map(([u,p])=>a`<tr><td>${u}</td><td class="num"><b>${oe(p.last)}</b></td>
              <td class="num">${oe(p.min)}</td><td class="num">${oe(p.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?a`<h4 class="small">Cited by</h4>${n.cited_by.map(u=>a`<p class="small"><${I} spec=${M("note",u.type)} /> ${u.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(u=>a`<div class="event small"><span class="muted num">${u.t?.slice(5,16).replace("T"," ")}</span>
        <${k} name=${yt(u.type)} size=${14} /><span>${u.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(s?.lines??[]).join(`
`)}</pre>
  </div>`}function ia({path:e}){let t=x(rt(e)).data,n=x(Kn(e)).data;return a`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?a`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(s=>!String(s.state??"").startsWith("superseded")).map(s=>a`<${ut} key=${s.id} note=${s} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(s=>a`<div class="event small"><span class="muted num">${s.t?.slice(5,16).replace("T"," ")}</span>
        <${k} name=${s.kind==="note"?"file-text":yt(s.type)} size=${14} />
        <span>${s.run?a`<a href=${ue(s.run)}>${s.run.slice(-8)}</a> `:null}${s.description??s.type}</span></div>`)}
  </div>`}function mt(e,t){let n=x(e),s=L(null);return n.status!=="loading"&&(s.current={scope:t,result:n}),n.status==="loading"&&s.current?.scope===t?s.current.result:n}var Tt=null;function ds(e){Tt?.();let t=document.querySelector(".main");if(!e||!t)return;let n=e.getBoundingClientRect().top,s=new ResizeObserver(()=>{e.isConnected&&(t.scrollTop+=e.getBoundingClientRect().top-n)});for(let o of t.children)s.observe(o);let r=["wheel","touchmove","keydown","pointerdown"],i=()=>{s.disconnect(),clearTimeout(c);for(let o of r)removeEventListener(o,i);Tt=null},c=setTimeout(i,5e3);for(let o of r)addEventListener(o,i,{passive:!0});Tt=i}var Mt=["failed","killed","lost"];function Nt(e){let t=ke(e.path),n=t==="."?e.path:e.path.slice(t.length+1),s=G(e.path)?[]:n.split("/"),r=s.length&&se(s[s.length-1])?s[s.length-1]:null,i=s.slice(0,-1),c=o=>[...t==="."?[]:[t],...i.slice(0,o+1)].join("/");return a`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${s.length?a`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${i.map((o,l)=>a`<span>/</span><a href=${S(c(l))}>${o}</a>`)}
    </nav>
    ${r?a`<${da} id=${r} scope=${e.path} />`:a`<${la} path=${e.path} />`}
    ${e.finding?a`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function la({path:e}){let t=P(x(Ne(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return a`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=Mt.reduce((r,i)=>r+(t[i]??0),0);return a`
    <h1 class="page-title title" tabindex="-1">${n} <${I} spec=${M("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?a`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?a`<span><b>${t.finished}</b> finished</span>`:null}
      ${s?a`<span class="tone-bad" data-tip=${Mt.filter(r=>t[r]).map(r=>`${t[r]} ${r}`).join(", ")}>
            <${k} name="circle-x" size=${15} /> <b>${s}</b> ${s===1?Mt.find(r=>t[r]):"ended early"}</span>`:null}
      ${t.notes?a`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${ms} path=${e} />
    </p>`}function us({path:e}){let t=P(x(Ne(e)).data)[0]??null,n=x(t?.proposal?Bn(e):null).data,s=x(t?.proposal?An(e):null).data;if(!t?.proposal)return null;let r=s?.proposal?.rationale,i=s?.versions?.find(l=>l.version===s.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[c,o]=Et(n?.progress?.text??t.progress);return a`<${O} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ye} value=${t.proposal} label="the proposal's statement" locked=${s?i:"Loading the proposal\u2026"}
          render=${l=>a`<span data-tip=${i?void 0:r}>${l}</span>`}
          onSave=${l=>Ln(e,l)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(l=>{let d=M("result",l.result),v=mn(l),u=v?`${d.label}: ${v}`:d.label;return a`<span class=${`check small tone-${d.tone}`} key=${l.name} data-tip=${u}
              aria-label=${`${l.name}: ${u}`} tabindex="0"><${k} name=${d.icon} size=${14} />${l.name}</span>`})}
        ${n?.provisional||c?a`<span class="small">
              ${n?.provisional?a`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${c?a`<span class="muted" data-tip=${o}>${n?.provisional?" \xB7 ":""}${c}</span>`:null}
            </span>`:null}
      </div>
      <${ca} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function ca(e){let t=x(e.verdict?rt(e.path):null).data;if(!e.verdict)return a`<p class="verdict-line muted">no verdict yet</p>`;let n=M("verdict",e.verdict),s=(t?.entries??[]).find(i=>i.type==="verdict"&&(i.group??e.path)===e.path),r=s?be(s.id):null;return a`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${k} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${s?a`<span class="small muted" data-tip=${r}>verdict${s.meta?.author?` by ${s.meta.author}`:""}${r?` \xB7 ${F(r)}`:""}</span>`:null}
  </p>`}function da({id:e,scope:t}){let n=x(De(e,t)).data;if(!n)return a`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=n.run,r=()=>{navigator.clipboard?.writeText(s.id)};return a`
    <h1 class="page-title title" tabindex="-1"><${ye} value=${s.name??s.id} label="the run's name" class="title-edit"
        onSave=${i=>In(s.id,t,i.trim())} />
      <${I} spec=${M("run",s.status)} word /></h1>
    ${s.error?a`<p class="bad-text" data-tip=${s.error}>${s.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${xe(s.steps)}</b> steps</span>
      <span><b>${Ce(s.duration_s)}</b></span>
      ${n.progress?a`<${ua} run=${s} progress=${n.progress} />`:null}
      <span data-tip=${s.created_at}>${F(s.created_at)}</span>
      <${ms} path=${t} />
      <${V} icon="copy" label=${`Copy the run id ${s.id}`} onClick=${r} />
      <${Qe} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${ma(s).map(([i,c])=>a`<tr><td class="muted">${i}</td><td>${c}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>R(S(t,{run:s.id}),{replace:!0})}>
            <${k} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${k} name="copy" size=${15} /> Copy the run id</button>
          ${s.git?.commit?a`<button type="button" onClick=${()=>navigator.clipboard?.writeText(s.git.commit)}>
            <${k} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?a`<div class="checks">
          ${n.proposals.map(i=>{let c=M("result",i.check);return a`<a class=${`check small tone-${c.tone}`} href=${S(i.group)} data-tip=${i.statement}>
              <${k} name=${c.icon} size=${14} />${i.group==="."?"own proposal":i.group}
              ${i.verdict?a`<${I} spec=${M("verdict",i.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function ua({run:e,progress:t}){let{epoch:n,total:s,fraction:r,steps_per_epoch:i}=t,c=e.status==="running"&&r!==null&&i&&e.steps_per_s?Ce((1-r)*s*i/e.steps_per_s):null;return a`<span>epoch <b>${n}</b>${s?` of ${s}`:""}${r===null?"":` \xB7 ${Math.round(r*100)} % through`}${c?` \xB7 about ${c} left`:""}</span>`}function ms({path:e}){let t=te(e).main,n=mt(xt(e,t),e).data?.summary;if(!n)return null;let s=Object.entries(n.config??{}).map(([c,o])=>`${bt(c)} ${oe(o)}`).join(", "),r=se(e.split("/").pop()??""),i=`${n.stat} of ${n.metric} over ${r?"the run":"all runs"}${s?` (${s})`:""}`;return a`<span data-tip=${i}>
    best <b>${n.label??bt(`metric.${n.metric}.${n.stat}`)} ${oe(n.value)}</b>
    ${r?null:a` · <a href=${ue(n.run)}>${n.name}</a>`}
  </span>`}function ma(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,s])=>[n,String(s)])}var Dt=80;function ps({node:e}){let t=J("main"),n=J(e.data?.keys?"keys":""),s=e.props.mode==="run",r=e.props.title??(s?"Config":"Hyperparameters");return a`<${Ae} id=${`config:${e.id}`} title=${r} open=${e.props.open} result=${t}>
    ${t.data?s?a`<${nt} config=${t.data.config} varying=${Fe(n.data)} />`:a`<${pa} rows=${t.data.config?.rows??[]} />`:a`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function pa({rows:e}){let t=new Set(Fe({config:{rows:e}})),n=e.filter(([s])=>t.has(s.replace(/^config\./,"")));return n.length?a`<table class="kv small">${n.map(([s,,r])=>{let i=Array.isArray(r)?r.map(oe).join(", "):`${oe(r.min)} \u2026 ${oe(r.max)} \xB7 ${r.distinct} values`;return a`<tr><td data-tip=${s}>${s.replace(/^config\./,"")}</td>
      <td data-tip=${i.length>Dt?i:void 0}>${i.length>Dt?`${i.slice(0,Dt-1)}\u2026`:i}</td></tr>`})}</table>`:a`<p class="muted small">No config differs between the runs.</p>`}var $s=15e3;function fs({node:e}){let t=Y(U),n=le(),[s,r]=tn(),i=e.props.code,c=x(r&&i?{method:"code",params:i,scope:null}:null),[o,l]=y(null),[d,v]=y(120),[u,p]=y({error:null,warnings:[]}),h=w=>{me&&console.error(`[block ${e.id}] ${w}`),p(m=>({...m,error:w}))},g=L(()=>{});T(()=>{if(!o)return;let w=!0;Le.n++;let m=()=>{w&&Le.n--,w=!1};g.current=m;let $=setTimeout(()=>{w&&h(`no first render within ${$s/1e3} s`),m()},$s);return()=>{clearTimeout($),m()}},[o]),T(()=>{let w=o?.contentWindow;if(!w||c.status!=="ready")return;let m=D=>w.postMessage(D,"*"),$=new Map,b=new gn,H=D=>{if(D.source!==w)return;let C=D.data;switch(C.type){case"hello":m({type:"init",init:{id:e.id,code:c.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:en.value,pair:Xe.value,colormaps:Oe.value,prefs:Ke(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!$n.has(C.call.method)){m({type:"result",id:C.id,result:{status:"error",data:null,error:`${C.call.method} is not available in a custom block`,refreshing:!1}});break}$.get(C.id)?.(),$.set(C.id,Ft(C.call,ee=>m({type:"result",id:C.id,result:ee})));break;case"unsub":$.get(C.id)?.(),$.delete(C.id);break;case"navigate":C.url.startsWith("/")&&R(C.url);break;case"height":b.accept(performance.now())?v(Math.max(40,C.height)):B("its height keeps changing, so it is fixed at its last height");break;case"chrome":p(ee=>({...ee,own:C.own}));break;case"ready":p(ee=>({...ee,blank:C.blank,overflow:C.overflow})),g.current();break;case"warn":B(C.message);break;case"hover":ht.set(C.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(C.prefs)&&A.set(C.prefs);break;case"download":case"snapshot":C.href?fn(C.href,C.name)?performance.now()-j>1e3&&(j=performance.now(),Be().download(C.href,C.name)):B(`a download of ${C.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":Be().figure(C.spec,C.name).catch(ee=>B(`the PDF failed: ${ee.message}`));break;case"expand":hn(C.node)&&Be().expand(C.node,t);break;case"error":h(C.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,E)),g.current();break;default:break}},B=D=>{me&&console.warn(`[block ${e.id}] ${D}`),p(C=>C.warnings.includes(D)?C:{...C,warnings:[...C.warnings,D]})},j=-1/0,A=Ke(t.path),X=ht.subscribe(D=>m({type:"hover",run:D})),_=A.subscribe(D=>m({type:"prefs",prefs:D}));return addEventListener("message",H),m({type:"ping"}),()=>{X(),_(),removeEventListener("message",H);for(let D of $.values())D()}},[c.status,c.data?.code,o]),T(()=>{let w={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};o?.contentWindow?.postMessage(w,"*")},[t.names,t.colors,t.metrics,o]),T(()=>Oe.subscribe(w=>o?.contentWindow?.postMessage({type:"colormaps",colormaps:w},"*")),[o]),T(()=>{n&&o?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let E=typeof i=="object"?i.path??i.block:String(i??"");nn(e.id,{png:()=>o?.contentWindow?.postMessage({type:"snapshot"},"*")});let f=r&&c.status==="ready"&&!u.error;return a`<div ref=${s} class="custom-block">
    ${u.own?null:a`<div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${f?a`<span class="chart-tools">
            <${V} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>o?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?a`<${V} icon="x" label="Close (Esc)" onClick=${()=>ze.set(null)} />`:a`<${V} icon="maximize" label="Expand" onClick=${()=>Be().expand(e,t)} />`}
          </span>`:null}
    </div>`}
    <${ae} caption=${e.props.expanded?void 0:e.props.caption} result=${c}>
      ${u.error?a`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${E})</span>
            <pre class="code">${u.error}</pre>
          </div>`:null}
      ${u.warnings.map(w=>a`<${z} kind="warning">${w}<//>`)}
      ${f?a`<div class="custom-frame" data-frame-blank=${u.blank?"1":void 0} data-frame-overflow=${u.overflow?"1":void 0}>
            <iframe key=${c.data.code} ref=${l} sandbox="allow-scripts" ...${$a()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${d}px`} />
          </div>`:null}
    <//>
  </div>`}function $a(){if(!!1)return{src:Kt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function hs({node:e}){let t=J("main"),n=Y(U),s=t.data?.entries??[];return a`<${ae} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!s.length?a`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${s.map(r=>a`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Ut(_e(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${Ie?"eager":"lazy"} />
          <figcaption class="small">step ${xe(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function gs({node:e}){let t=J("main"),n=t.data?.entries??[];return a`<${ae} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?a`<${z}>No text logged.<//>`:null}
    ${n.map(s=>a`<div class="text-entry" key=${`${s.run}/${s.step}`}>
        <div class="muted small">step ${xe(s.step)}${s.caption?` \xB7 ${s.caption}`:""}</div>
        <pre class="code">${s.text??""}</pre>
      </div>`)}
  <//>`}function vs({node:e}){let n=`section.${Y(U).path}:${e.id}`,[s,r]=y(()=>Ie||ge(n,e.props.open!==!1)),i=()=>{ve(n,!s),r(!s)},c=a`${(e.children??[]).map(d=>a`<${ie} key=${d.id} node=${d} />`)}`,o=Y(Ze);if(!e.props.title)return a`<div class="stack">${c}</div>`;let l=o===e.props.title.toLowerCase();return a`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${s} aria-label=${l?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${l?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${i}>
      <${k} name=${s?"chevron-down":"chevron-right"} size=${16} />${l?null:e.props.title}
    </button>
    ${s?a`<div class="stack">${c}</div>`:null}
  </div>`}function bs({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return a`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>a`<${ie} key=${n.id} node=${n} />`)}
  </div>`}function Rt({node:e,after:t}){let n=Y(U),s=te(n.path),r=e.props.min_width??320,i=e.props.columns,c=i?`grid-template-columns: repeat(${i}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${r}px, 100%), 1fr))`,o=e.children??[],l=o.filter(u=>s.removed.includes(u.id)).map(u=>u.id),d=un(o.filter(u=>!l.includes(u.id)),s.order[e.id]),v=(u,p)=>{let h=d.map(g=>g.id).filter(g=>g!==u);if(h.splice(h.indexOf(p),0,u),cn(n.path,e.id,h),e.id===rn){let g=f=>o.find(w=>w.id===f)?.data?.main?.params?.y?.[0],E=h.map(f=>n.pins.find(w=>w.y===g(f))).filter(f=>!!f);ln(n.path,[...E,...n.pins.filter(f=>!E.includes(f))])}};return a`<div class="grid" style=${c}>
    ${d.map(u=>a`<${fa} key=${u.id} node=${u} path=${n.path} span=${s.spans[u.id]??u.props.span??1}
      columns=${i} onDrop=${p=>p!==u.id&&v(p,u.id)} />`)}
    ${t??null}
    ${l.length?a`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ue(n.path,l)}>${l.length} hidden · show</button></div>`:null}
  </div>`}var Pt=[1,2,"full"];function fa(e){let[t,n]=y(!1),s=Pt[(Pt.indexOf(e.span)+1)%Pt.length],r=i=>i==="full"?"full width":`${i} column${i===1?"":"s"}`;return a`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${i=>{i.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${i=>{i.preventDefault(),n(!1),e.onDrop(i.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${i=>i.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${k} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(s)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>dn(e.path,e.node.id,s)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ie} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Lt({root:e}){let t=Y(U),n=te(t.path),s=x({method:"keys",params:{from:t.path},scope:t.path}).data,r=e.props.template;if(!r||!1)return null;let i=new Set(n.removed),c=new Set([...t.charted].filter(([h])=>!i.has(h)).flatMap(([,h])=>h)),o=n.added.filter(h=>!c.has(h)).map(h=>({block:"line",id:`added-${h}`,props:{y:h},data:{main:{...r,params:{...r.params,y:[h]}}}})),l=new Set([...c,...o.filter(h=>!i.has(h.id)).map(h=>h.props.y)]),d=(s?.metrics?.rows??[]).map(h=>h[0]).filter(h=>!l.has(h));if(!s||!(d.length||o.length))return null;let v=h=>[...t.charted].find(([g,E])=>i.has(g)&&E.includes(h))?.[0]??o.find(g=>i.has(g.id)&&g.props.y===h)?.id,u=h=>{let g=v(h);g?Ue(t.path,[g]):tt(t.path,E=>({added:[...E.added,h]}))},p=d.length?a`<div class="add-chart">
        <span class="add-chart-label"><${k} name="plus" size=${16} /> Add a chart</span>
        <${et} single options=${d} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([h])=>u(h)} />
      </div>`:null;return a`<${O}><${Rt} node=${{block:"grid",id:"added",props:{},children:o}} after=${p} /><//>`}function ys({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[s,r]=y(()=>t.find(o=>o.id===n())?.id??t[0]?.id),i=o=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(o)}`),r(o)},c=t.find(o=>o.id===s)??t[0];return Ie?a`<div class="stack">${t.map(o=>a`<${ie} key=${o.id} node=${o} />`)}</div>`:a`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(o=>a`<button type="button" role="tab" id=${`tab-${o.id}`} aria-selected=${o.id===c?.id}
          aria-controls=${`panel-${o.id}`} onClick=${()=>i(o.id)}>${o.props.title??o.id}</button>`)}
    </div>
    ${c?a`<div class="stack" role="tabpanel" id=${`panel-${c.id}`} aria-labelledby=${`tab-${c.id}`}>
          ${(c.children??[]).map(o=>a`<${ie} key=${o.id} node=${o} />`)}
        </div>`:null}
  </div>`}var ws={section:vs,row:bs,grid:Rt,line:Cn,table:Nn,stat:Mn,images:hs,text:gs,proposal:es,note:ls,output:os,config:ps,memory:ts,groups:ns,notes:ss,tabs:ys,scatter:Sn,bar:En,histogram:Tn,data_table:yn,timeline:wn,custom:fs,markdown:is},ha=new Set(["line","scatter","bar","histogram"]);function ie({node:e}){return ha.has(e.block)?a`<${ga} node=${e} />`:a`<${wt} node=${e} blocks=${ws} />`}function ga({node:e}){let t=Y(U);return te(t.path).removed.includes(e.id)?a`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ue(t.path,[e.id])}>1 hidden · show</button></div>`:a`<${wt} node=${e} blocks=${ws} />`}function ks(e,t){let n=e.split(`
`),s=t.split(`
`),r=n.length,i=s.length,c=Array.from({length:r+1},()=>new Uint32Array(i+1));for(let v=r-1;v>=0;v--)for(let u=i-1;u>=0;u--)c[v][u]=n[v]===s[u]?c[v+1][u+1]+1:Math.max(c[v+1][u],c[v][u+1]);let o=[],l=0,d=0;for(;l<r&&d<i;)n[l]===s[d]?(o.push({kind:"same",text:n[l]}),l++,d++):c[l+1][d]>=c[l][d+1]?o.push({kind:"removed",text:n[l++]}):o.push({kind:"added",text:s[d++]});for(;l<r;)o.push({kind:"removed",text:n[l++]});for(;d<i;)o.push({kind:"added",text:s[d++]});return o}function xs(e,t=3){let n=[],s=0;for(;s<e.length;){if(e[s].kind!=="same"){n.push(e[s++]);continue}let r=s;for(;r<e.length&&e[r].kind==="same";)r++;let i=s===0?0:t,c=r===e.length?0:t;r-s>i+c+1?n.push(...e.slice(s,s+i),{kind:"skip",count:r-s-i-c},...e.slice(r-c,r)):n.push(...e.slice(s,r)),s=r}return n}var _t={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function Cs(e){if(_t[e.block])return _t[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(r=>_t[r.block])),[s]=n;if(n.size===1&&s)return s}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function pt(e){let t=x(je(e.path)),n=le(),s=P(t.data),r=Re(()=>Je(s.map(p=>p["run.id"]),n),[t.data,n]),i=Re(()=>new Map(s.map(p=>[p["run.id"],p["run.name"]??p["run.id"]])),[t.data]),c=te(e.path),o=e.plain?"view plain":"sections view";if(!e.view)return a`<div class=${o}>${e.before}
      ${e.plain?a`<div class="skeleton late" style="block-size: 320px"></div>`:a`<${O} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let l=e.view.view,d={path:e.path,colors:r,names:i,metrics:e.view.metrics??{},charted:It(l),pins:c.main??e.view.pins??[]};if(e.plain)return a`<div class=${o}><${U.Provider} value=${d}><${ie} node=${l} /><//></div>`;let v=l.block==="section"&&!l.props.title?l.children??[]:[l],u=v.map(p=>It(p).size>0).lastIndexOf(!0);return a`<div class=${o}>${e.before}
    <${U.Provider} value=${d}>
      ${v.map((p,h)=>{let g=Cs(p);return a`<${Bt} key=${p.id}><${O} label=${g}><${Ze.Provider} value=${g}><${ie} node=${p} /><//><//>
          ${h===u?a`<${Lt} root=${l} />`:null}<//>`})}
      ${u===-1?a`<${Lt} root=${l} />`:null}
    <//>
  </div>`}function It(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])It(n,t);return t}function Ss(e){if(null)return a`<div class="view-source small"><${k} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=N(W),s=n.page==="group"&&n.version,r=t.versions?a`<a href=${S(e.path,{history:!0})}><${k} name="history" size=${14} /> history (${t.versions})</a>`:null,i;switch(t.source){case"draft":i=a`draft <b>${t.draft}</b>`;break;case"view":i=a`${t.title?a`<em>${t.title}</em> · `:null}saved ${F(be(t.version))} by ${t.author??"unknown"}`;break;default:i=a`the built-in view`}return a`<div class="view-source small">
    <${k} name="layout" size=${14} /><span>${i}</span>
    ${s?a`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!s?a`<${va} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||s?null:a`<${ba} path=${e.path} />
        <${ya} path=${e.path} view=${t} />`}
  </div>`}function va(e){let[t,n]=y(null),s=e.outdated.map(i=>i.name).join(", ");return a`<button type="button" class="link small" onClick=${async()=>{n(null);try{await On(e.path)}catch(i){n(i.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${s} exists; update re-pins this view to it (a new version)`}>
      <${k} name="update" size=${14} /> update ${s}</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function ba(e){let[t,n]=y(null);return a`<button type="button" class="link small" onClick=${async()=>{n(null);try{Me.set(await at(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${k} name="file-text" size=${14} /> add text</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function ya(e){let t=te(e.path),n=on(t),[s,r]=y(!1),[i,c]=y(e.view.title??""),[o,l]=y(e.view.finding??""),[d,v]=y(null),[u,p]=y(!1);if(!n&&!s)return null;let h=async g=>{g.preventDefault(),p(!0),v(null);try{let E={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await K("save_view",{path:e.path,prefs:E,title:i,finding:o}),tt(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),Ee(f=>["view","view_history","summary"].includes(f.method)&&f.scope===e.path),r(!1)}catch(E){v(E.message)}finally{p(!1)}};return s?a`<form class="save-form" onSubmit=${h}>
    <${He} label="Title"><input value=${i} onInput=${g=>c(g.target.value)} /><//>
    <${He} label="Finding"><input value=${o} placeholder="the key result in one sentence"
        onInput=${g=>l(g.target.value)} /><//>
    <div class="save-actions">
      <${re} type="submit" icon=${u?"hourglass":"save"} disabled=${u}>${u?"Saving\u2026":"Save as view"}<//>
      <${re} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${d?a`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:a`<${re} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function Es(e){let t=x(jn(e.path)),n=t.data?.entries??[],[s,r]=y(null),i=s??n.slice(0,2).map(o=>o.version).reverse(),c=o=>{let l=i.includes(o)?i.filter(d=>d!==o):[...i,o].slice(-2);r(l.sort())};return t.status==="error"?a`<${z} kind="error">${t.error}<//>`:a`<section class="history">
    <h2 class="history-title heading"><${k} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?a`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((o,l)=>a`<li key=${o.version} class=${i.includes(o.version)?"picked":""}>
          <label><input type="checkbox" checked=${i.includes(o.version)} onChange=${()=>c(o.version)} />
            <span class="num muted" data-tip=${o.version}>${F(o.time)}</span>
            <b>${o.title??"untitled"}</b><span class="muted">${o.author??""}</span>
            ${o.message?a`<span>${o.message}</span>`:null}</label>
          <a href=${l===0?S(e.path):S(e.path,{version:o.version})}
            onClick=${d=>{d.preventDefault(),R(l===0?S(e.path):S(e.path,{version:o.version}))}}>${l===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${i.length===2?a`<${wa} path=${e.path} a=${i[0]} b=${i[1]} />`:null}
  </section>`}function wa(e){let t=o=>({method:"view_show",params:{group:e.path,version:o},scope:e.path}),n=x(t(e.a)).data,s=x(t(e.b)).data,r=x($e(e.path,e.a)).data,i=x($e(e.path,e.b)).data,c=n&&s?xs(ks(n.yaml,s.yaml)):[];return a`<div class="compare">
    <h3 class="block-title heading">Changes from ${F(be(e.a))} to ${F(be(e.b))}</h3>
    <pre class="diff code">${c.map(o=>o.kind==="skip"?a`<div class="diff-skip">⋯ ${o.count} unchanged lines</div>`:a`<div class=${`diff-${o.kind}`}>${o.kind==="added"?"+ ":o.kind==="removed"?"\u2212 ":"  "}${o.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${pt} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${i?.title??e.b}</h3><${pt} path=${e.path} view=${i} plain /></div>
    </div>
  </div>`}function Ts(e){return Gn(e.path),e.history?a`<div class="page"><div class="sections">
      <${O} label=${Ms(e.path)}><${Nt} path=${e.path} /><//>
      <${O} label="history"><${Es} path=${e.path} /><//>
    </div></div>`:a`<div class="page">
    <${ka} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function ka(e){let t=te(e.path).main,n=mt($e(e.path,e.version,e.draft,t),`${e.path}|${e.version}|${e.draft}`);T(()=>{n.status==="ready"&&requestAnimationFrame(qt)},[n.status==="ready"]),T(()=>{let r=i=>ds(i.target.closest?.(".chart-frame")??null);return addEventListener("click",r,!0),()=>removeEventListener("click",r,!0)},[]);let s=a`
    <${O} label=${Ms(e.path)}>
      <${Nt} path=${e.path} finding=${n.data?.finding} />
      ${n.data?a`<${Ss} path=${e.path} view=${n.data} />`:null}
    <//>
    ${se(e.path.split("/").pop()??"")?null:a`<${us} path=${e.path} />`}`;return n.status==="error"?a`<div class="sections">${s}
      <${O} label="view">
        ${xa(e.path,n.error)?a`<${z} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:a`<${z} kind="error">${n.error}<//>`}
      <//>
    </div>`:a`<${pt} path=${e.path} view=${n.data} before=${s} />`}function Ms(e){return se(e.split("/").pop()??"")?"run":"group"}function xa(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Ns(e){T(()=>{Se($e(e.id)).then(n=>R(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=x($e(e.id));return t.status==="error"?a`<div class="page"><${z} kind="error">${t.error}<//></div>`:a`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var Ca={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Ot=20,Pe=-1,Sa=[["day",86400],["week",7*86400],["month",30*86400]];function Ps(e){let t=P(x(ce()).data).map(o=>o.path),n=x({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),s=x({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Ve("Timeline",P(n.data).filter(o=>o["run.status"]==="running").length);let r=Date.now()/1e3,i=P(n.data).filter(o=>o["run.created_at"]).map((o,l)=>({id:o["run.id"],name:o["run.name"]??o["run.id"],group:o["run.group"],status:o["run.status"],start:Date.parse(o["run.created_at"])/1e3,end:o["run.ended_at"]?Date.parse(o["run.ended_at"])/1e3:r,lane:l})),c=(s.data?.entries??[]).map(o=>({id:o.id,type:o.type,group:o.group,description:o.description,t:Date.parse(be(o.id))/1e3}));return a`<div class="page timeline-page"><div class="sections">
    <${O} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${He} label="Group" inline>
          <select value=${e.from} onChange=${o=>R(qe(o.target.value),{replace:!0})}>
            ${t.map(o=>a`<option value=${o}>${o==="."?"everything":o}</option>`)}
          </select><//>
        <span class="muted small">${i.length} runs · ${c.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${O} label="runs">
      ${n.status==="error"?a`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&s.data?a`<${Ea} bars=${i} marks=${c} />`:a`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function Ea(e){let t=le(),n=L(null),s=[...e.bars.flatMap(f=>[f.start,f.end]),...e.marks.map(f=>f.t)],r=s.length?Ds(Math.min(...s),Math.max(...s)):Ds(Date.now()/1e3-86400,Date.now()/1e3),[i,c]=y(r),o=e.bars.length,l=Math.min(900,Math.max(160,(o+1.5)*Ot+40)),v=kn(n,xn,t?(f=>{let w=vn(i[0],i[1]),m=b=>f.colors[Ca[b]??"muted"],$=b=>f.colors[b==="verdict"?"good":b==="decision"?"accent":b==="question"?"warn":"muted"];return{style:Qt(f),height:l,x:{range:i,log:!1,format:b=>bn(b,w.step),label:"",splits:w.at},y:{range:[Pe-.8,o+.5],log:!1,reverse:!0,label:"",size:150,splits:o<=40?[Pe,...e.bars.map(b=>b.lane)]:[Pe],format:b=>b===Pe?"notes":Pa(e.bars[Math.round(b)]?.name??"")},draw:({ctx:b,x:H,y:B,px:j,focused:A})=>{let X=Ot*.62*j;for(let _ of e.bars){let D=H(_.start),C=Math.max(3*j,H(_.end)-D);b.fillStyle=A!==null&&A!==_.id?Zt(m(_.status),.35):m(_.status),b.beginPath(),b.roundRect(D,B(_.lane)-X/2,C,X,3*j),b.fill()}for(let _ of e.marks){let D=H(_.t),C=B(Pe),ee=(A===_.id?6:4.5)*j;b.fillStyle=$(_.type),b.beginPath(),b.moveTo(D,C-ee),b.lineTo(D+ee,C),b.lineTo(D,C+ee),b.lineTo(D-ee,C),b.closePath(),b.fill()}},hit:(b,H,B,j)=>{if(Math.abs(H-j(Pe))<Ot/2){let _=Da(e.marks,D=>Math.abs(B(D.t)-b),8);return _?{key:_.id,rows:Ma(_)}:null}let A=Math.round((H-j(0))/(j(1)-j(0))),X=e.bars.find(_=>_.lane===A&&B(_.start)-3<=b&&b<=Math.max(B(_.end),B(_.start)+3)+3);return X?{key:X.id,rows:Ta(X)}:null},onClick:b=>{let H=e.marks.find(B=>B.id===b);H?R(S(H.group,{drawer:!0})):R(ue(b))}}})(t):null,[i,e.bars,e.marks],t),u=f=>{if(!v.current)return;f.preventDefault();let w=v.current.xAt(f.clientX),m=Math.exp(f.deltaY*.0015);c(([$,b])=>zt([w-(w-$)*m,w+(b-w)*m],r))},p=L(null),h=f=>p.current={x:f.clientX,range:i},g=f=>{if(!p.current||!v.current||!(f.buttons&1))return;let w=(f.clientX-p.current.x)*v.current.xPerPixel(),[m,$]=p.current.range;Math.abs(f.clientX-p.current.x)>3&&c(zt([m-w,$-w],r))},E=Math.max(...s,Date.now()/1e3);return a`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Sa.map(([f,w])=>a`<button type="button" role="radio" aria-checked=${Math.abs(i[1]-i[0]-w)<1}
          onClick=${()=>c(zt([E-w,E+w*.02],[Math.min(r[0],E-w),r[1]]))}>last ${f}</button>`)}
      <button type="button" role="radio" aria-checked=${i[0]===r[0]&&i[1]===r[1]} onClick=${()=>c(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${l}px`}
      onWheel=${u} onPointerDown=${h} onPointerMove=${g} onPointerUp=${()=>p.current=null}></div>
    <p class="muted small">${Na(t)}</p>
  </div>`}function Ta(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:F(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Ce(e.end-e.start),color:null}]}function Ma(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:F(new Date(e.t*1e3).toISOString()),color:null}]}function Na(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Da(e,t,n){let s=null,r=n;for(let i of e){let c=t(i);c<r&&([s,r]=[i,c])}return s}function Ds(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function zt([e,t],n){let s=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-s));return[r,r+s]}function Pa(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function Rs(){let e=N(ze),t=L(null);if(T(()=>{let r=t.current;if(!r||!e)return;r.showModal();let i=()=>ze.set(null);return r.addEventListener("close",i),()=>r.removeEventListener("close",i)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},s=String(n.props.title??n.props.y??"Chart");return a`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${s} closedby="any">
    <${U.Provider} value=${e.view}><${ie} node=${n} /><//>
  </dialog>`}function Ls(e,t){let n=e.toLowerCase(),s=t.toLowerCase();if(!n)return 1;let r=s.indexOf(n);if(r>=0)return 100-Math.min(r,50)-s.length/100;let i=0,c=0;for(let o of s)if(o===n[i]?i++:i>0&&c++,i===n.length)return 40-Math.min(c,39);return 0}function Is(e){let[t,n]=y(e.query),[s,r]=y(0),i=L(null),c=P(x(ce()).data),o=P(x(ot()).data);T(()=>{let m=i.current;m.showModal();let $=()=>Q.set(null);m.addEventListener("close",$);let b=!1,H=A=>{let X=m.getBoundingClientRect();return A.clientX<X.left||A.clientX>X.right||A.clientY<X.top||A.clientY>X.bottom},B=A=>b=H(A),j=A=>b&&H(A)&&m.close();return"closedBy"in HTMLDialogElement.prototype||(m.addEventListener("pointerdown",B),m.addEventListener("pointerup",j)),()=>{m.removeEventListener("close",$),m.removeEventListener("pointerdown",B),m.removeEventListener("pointerup",j)}},[]);let l=()=>i.current?.close(),d=m=>()=>R(m),v=W.value,u=v.page==="group"?v.path:".",p=(m,$,b,H)=>({section:"Commands",label:m,detail:$,sym:{icon:b,tone:"muted",label:m},run:H}),g=[...c.map(m=>({section:"Groups",label:m.path==="."?"local":m.path,detail:`${m.runs} runs${m.proposal?` \xB7 ${m.proposal}`:""}`,sym:M("research",m.status),run:d(S(m.path))})),...o.map(m=>({section:"Runs",label:m["run.name"]??m["run.id"],detail:`${m["run.status"]} \xB7 ${m["run.path"]}`,sym:M("run",m["run.status"]),run:d(S(m["run.path"]))})),p("Theme: light","","sun",()=>Ye("light")),p("Theme: dark","","moon",()=>Ye("dark")),p("Theme: follow the system","","monitor",()=>Ye("system")),p("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),p("Show notes and timeline","i","file-text",d(S(u,{drawer:!0}))),p("Show or hide the sidebar","\u2318B","panel-left",()=>Z.set(!Z.value)),p(ne.value?"Resume live updates":"Pause live updates","p",ne.value?"play":"pause",()=>ne.set(!ne.value)),p("Keyboard shortcuts","?","keyboard",()=>fe.set(!0)),p("Settings","","settings",d("/settings/appearance"))].map(m=>({it:m,s:Math.max(Ls(t,m.label),Ls(t,m.detail)*.5)})).filter(m=>m.s>0).sort((m,$)=>$.s-m.s||_s(m.it.section)-_s($.it.section)).slice(0,60).map(m=>m.it),E=m=>{m&&(l(),m.run())},f=m=>{if(m.key==="ArrowDown")r(Math.min(g.length-1,s+1));else if(m.key==="ArrowUp")r(Math.max(0,s-1));else if(m.key==="Enter")E(g[s]);else return;m.preventDefault()},w="";return a`<dialog class="sheet" ref=${i} aria-label="Search" closedby="any">
    <div class="palette-input"><${k} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${g[s]?`pal-${s}`:void 0}
        onInput=${m=>{n(m.target.value),r(0)}} onKeyDown=${f} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${g.map((m,$)=>{let b=m.section!==w&&!t?w=m.section:null;return a`${b?a`<li class="palette-head small" role="presentation">${b}</li>`:null}
          <li id=${`pal-${$}`} class="item" role="option" aria-selected=${$===s}
              onMouseMove=${()=>r($)} onClick=${()=>E(m)}>
            <${I} spec=${m.sym} /><span class="label">${m.label}</span><span class="detail small">${m.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function _s(e){return["Groups","Runs","Commands"].indexOf(e)}function $t(e,t=[]){let n=new Map,s=(o,l={})=>({path:o,name:o==="."?"local":o.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let o of e)n.set(o.path,s(o.path,o));(t.length===0||t.some(o=>o.name==="local"))&&!n.has(".")&&n.set(".",s("."));for(let o of t){let l=o.name==="local"?".":o.name;n.has(l)||n.set(l,s(l)),Object.assign(n.get(l),{state:o.state,error:o.error})}for(let o of n.values()){if(G(o.path))continue;let l=o.path.lastIndexOf("/"),d=l<0?".":o.path.slice(0,l);(n.get(d)??n.get(ke(o.path))??n.get(".")).children.push(o)}for(let o of n.values())o.children.sort((l,d)=>l.name.localeCompare(d.name));let i=[...n.values()].filter(o=>o.path!=="."&&G(o.path)).sort((o,l)=>o.name.localeCompare(l.name)),c=n.get(".");return c?[c,...i]:i}function Os(e,t,n,s=new Set){let r=[],i=n.toLowerCase(),c=o=>{(!i||o.path.toLowerCase().includes(i)||zs(o,i))&&(r.push(o),(i||(G(o.path)?!s.has(o.path):t.has(o.path)))&&o.children.forEach(c))};return e.forEach(c),r}function zs(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||zs(n,t))}function Bs(e,t){if(G(t))return e;let n=t.lastIndexOf("/"),s=n<0?".":t.slice(0,n),r=i=>i.path===s?i:i.children.map(r).find(c=>c)??null;return e.map(r).find(i=>i)?.children??[]}function As(e){return G(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Hs(){let e=N(W),t=x(ce()),[n,s]=y(()=>new Set(ge("open",[]))),[r,i]=y(()=>new Set(ge("closed-hosts",[]))),[c,o]=y(""),l=L(null),d=e.page==="group"?e.path:null,v=$t(P(t.data),t.data?.meta?.sources??[]),u=Os(v,_a(n,d),c,r),p=f=>G(f)?!r.has(f):n.has(f),h=(f,w)=>{let m=w??!p(f);if(G(f)){let b=new Set(r);m?b.delete(f):b.add(f),ve("closed-hosts",[...b]),i(b);return}let $=new Set(n);m?$.add(f):$.delete(f),ve("open",[...$]),s($)},g=L(d);return T(()=>{d!==g.current&&d&&!G(d)&&r.has(ke(d))&&h(ke(d),!0),g.current=d},[d]),a`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${k} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${c} aria-label="Filter groups"
        onInput=${f=>o(f.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${f=>{let w=[...l.current?.querySelectorAll("a.tree-item")??[]],m=w.indexOf(document.activeElement),$=u[m];switch(f.key){case"ArrowDown":w[Math.min(w.length-1,m+1)]?.focus();break;case"ArrowUp":w[Math.max(0,m-1)]?.focus();break;case"ArrowRight":$?.children.length&&h($.path,!0);break;case"ArrowLeft":$?.children.length&&p($.path)?h($.path,!1):$&&w[u.findIndex(b=>b.path===La($.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${u.map(f=>a`<${Ra} key=${f.path} node=${f} current=${f.path===d}
        open=${p(f.path)||!!c} onToggle=${()=>h(f.path)} />`)}
    </div>
  </nav>`}function Ra(e){let t=e.node,n=()=>Ge(t.path),s=t.children.length>0,r=t.state==="unreachable";return a`<a class=${`tree-item${e.current?" current":""}${G(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${s?e.open:void 0}
      style=${`padding-inline-start:${8+As(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${i=>{i.metaKey||i.ctrlKey||(i.preventDefault(),R(S(t.path)))}}>
    <span class="twisty" onClick=${i=>{i.preventDefault(),i.stopPropagation(),e.onToggle()}}>
      ${s?a`<${k} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${G(t.path)?a`<${I} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?a`<${I} spec=${M("run","running")} size=${14} />`:null}
      ${t.failed?a`<${I} spec=${{...M("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function La(e){if(G(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function _a(e,t){if(!t||t===".")return e;let n=new Set(e),s=t.split("/");for(let r=1;r<s.length;r++)n.add(s.slice(0,r).join("/"));return n}function Us(){let e=N(W),t=N(Z),n=N(Q),s=N(fe),r=L(null);T(()=>Wt(()=>r.current),[]),T(()=>(addEventListener("keydown",Ks),()=>removeEventListener("keydown",Ks)),[]);let i=e.page==="group"&&e.drawer,c;switch(e.page){case"group":c=a`<${Ts} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":c=a`<${Ns} id=${e.id} />`;break;case"settings":c=a`<${Xn} />`;break;case"timeline":c=a`<${Ps} key=${e.from} from=${e.from} />`;break;default:c=a`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return me||!1?a`<main class="main render-main" ref=${r}>${c}</main>`:a`<div class=${`shell${t?"":" no-sidebar"}${i?" with-drawer":""}`}>
    <${Jn} />
    ${t?a`<${Hs} />`:null}
    <main class="main" ref=${r}>${c}</main>
    ${i?a`<${cs} path=${e.path} run=${e.run} />`:null}
    <${Zn} />
    ${n!==null?a`<${Is} query=${n} />`:null}
    ${s?a`<${Oa} />`:null}
    <${Rs} />
  </div>`}function Ks(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),Q.set(Q.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Z.set(!Z.value);return}if(e.key==="Escape"){if(Q.value!==null||fe.value)return;let s=W.value;return s.page==="group"&&s.run?R(S(s.path,{drawer:!0}),{replace:!0}):s.page==="group"&&s.drawer?R(S(s.path),{replace:!0}):void 0}if(t||e.altKey||Wn(e)||Q.value!==null||fe.value)return;let n=W.value;switch(e.key){case"/":e.preventDefault(),Q.set("");break;case"?":fe.set(!fe.value);break;case"p":ne.set(!ne.value);break;case"i":n.page==="group"&&R(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Z.set(!Z.value);break;case"[":case"]":n.page==="group"&&Ia(n.path,e.key==="]"?1:-1);break}}async function Ia(e,t){let n=await Se(ce()),s=Bs($t(P(n),n?.meta?.sources??[]),e),r=s.findIndex(c=>c.path===e),i=s[r+t];i&&R(S(i.path))}function Oa(){let e=L(null);return T(()=>{let t=e.current;t.showModal();let n=()=>fe.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),a`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${lt.map(([t,n])=>a`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${re} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Xt();if(me){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(pe.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Le.n,Yt&&sn()}Dn();var za=K("meta").then(e=>(me&&(e={...e,settings:{...e.settings,theme_mode:pe.value}}),ct(e),e));!me&&!!1&&Vt(async()=>{let[e,t]=await Promise.all([za,K("meta")]);e.bundle!==t.bundle?location.reload():ct(t)});At(a`<${Us} />`,document.getElementById("app"));
