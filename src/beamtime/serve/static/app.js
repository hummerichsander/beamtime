import{$ as W,A as Wt,Aa as mn,B as me,Ba as pn,C as Ie,Ca as hn,D as qt,Da as gn,E as Xe,Ea as vn,F as ft,G as pe,Ga as bn,H as Zt,Ha as yn,I as ht,Ia as wn,J as Ye,Ja as kn,K as U,Ka as xn,L as Z,La as Sn,M as le,Ma as Cn,N as Je,Na as En,O as Qt,P as Oe,Q as ze,S as en,T as tn,U as w,V as L,W as Ze,X as ae,Y as z,Z as P,_ as Be,a as s,aa as nn,ba as I,ca as oe,d as K,da as Ae,e as Le,ea as gt,f as Ce,fa as Qe,g as $t,ga as et,h as x,ha as sn,i as Kt,ia as He,j as ne,ja as te,k as Ut,ka as tt,l as Ft,la as an,m as jt,ma as on,n as Ee,na as Ke,o as se,oa as rn,p as C,pa as ln,q as We,qa as cn,r as ue,ra as T,s as Re,sa as bt,t as ke,ta as Ue,u as V,ua as nt,v as q,va as yt,w as Gt,wa as dn,y as _,z as Vt,za as un}from"./chunks/chunk-WOC2LN7A.js";import{a as At,b as Ht}from"./chunks/chunk-O2K4N3UR.js";import{A as Yt,B as Jt,C as j,F as be,G as xe,H as Se,I as F,J as vt,U as $n,V as fn,c as zt,e as y,f as M,g as Bt,h as O,i as _e,j as J,m as we,n as N,o as ge,p as ve,u as Xt,w as qe}from"./chunks/chunk-24GOVU2B.js";import"./chunks/chunk-VC46IEJQ.js";function Te(e,t){Ee(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var wt=["notes","timeline","groups","check","card","memory_show","status"];async function st(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Te(e.group,wt)}async function Tn(e,t,n,a){await K("note_add",{group:e,type:t,description:n,body:a}),Te(e,wt)}async function Mn(e,t){await K("memory_update",{group:e,body:t}),Te(e,["memory_show","status"])}async function Nn(e,t){let n=await K("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([o])=>!["schema","author","user","supersedes"].includes(o)));await K("proposal_set",{group:e,proposal:{...a,statement:t}}),Te(e,["groups","proposal_show","check","summary"])}async function Dn(e){await K("note_rm",{note:e.id}),Te(e.group,wt)}async function Pn(e,t,n){await K("name",{run:e,name:n}),Te(t,["card","runs","groups","summary","series"])}async function at(e,t,n){let a=await K("view_text",{path:e,id:t,text:n});return Ee(o=>["view","view_history"].includes(o.method)&&o.scope===e),a.id}async function _n(e){await K("view_upgrade",{group:e}),Ee(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Me=new we(null);async function Ln(e,t){return await K("set",{key:e,value:t}),K("meta")}var ce=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),$e=(e,t=null,n=null,a=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...a?{metrics:a}:{}},scope:e}),kt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),Ne=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Rn=e=>({method:"check",params:{group:e},scope:e}),In=e=>({method:"proposal_show",params:{group:e},scope:e}),De=(e,t)=>({method:"card",params:{run:Re(e,t)},scope:t}),On=(e,t)=>({method:"output",params:{run:Re(e,t),tail:30},scope:t}),Fe=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),ot=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),zn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Bn=()=>({method:"status",params:{},scope:"."}),rt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function je(e){let t=He(e).value.main;for(let n of[$e(e,null,null,t),Ne(e),Fe(e),kt(e,t)])$t(n);Ce($e(e,null,null,t)).then(n=>{for(let a of An(n.view))$t(a)}).catch(()=>{})}function An(e){return e?[...Bs.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(An)]:[]}var Bs=new Set(["line","custom"]),Hn=e=>({method:"view_history",params:{group:e},scope:e});var xt="/static/favicon.svg",it=null;async function As(){if(it)return it;let e=new Image;e.src=xt,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let a=n.getContext("2d");if(!a)return xt;a.drawImage(e,0,0,t,t),a.beginPath(),a.arc(t-6,t-6,6,0,Math.PI*2);let o=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return a.fillStyle=o||"#2f5aa8",a.fill(),it=n.toDataURL("image/png"),it}function Hs(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=xt;return}As().then(n=>{t.type="image/png",t.href=n})}}function Ge(e,t=0){M(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,Hs(t>0)},[e,t])}function Kn(e){let t=se(e.split("/").pop()??""),n=x(t?null:Ne(e)),a=x(t?De(e.split("/").pop()??"",e):null),o=t?a.data?.run.name??a.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,r=t?a.data?.run.status==="running"?1:0:P(n.data)[0]?.running??0;Ge(o,r)}var Q=new we(ge("sidebar",!0)),ee=new we(null),fe=new we(!1),he=new we(null);Q.subscribe(e=>ve("sidebar",e));var Un=ge("visit",Date.now());ve("visit",Date.now());function Fn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var lt=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Ks=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function ct(e){he.set(e),Xe.set(e.theme),qe.set(e.colormaps),e.settings?.theme_mode&&pe.set(e.settings.theme_mode),ht()}var jn=0;async function St(e,t){let n=++jn;e==="theme_mode"&&(pe.set(t),ht());let a=await Ln(e,t);n===jn&&ct(a)}function Gn(){let e=N(pe),t=le(),n=N(he),[a,o]=y(null);Ge("Settings");let r=(l,d)=>{o(null),St(l,d).catch(v=>o(v.message))},c=n?.settings??{},i=(l,d,v)=>s`
    <label class="field-label small" for=${`setting-${l}`}>${d}</label>
    <span class="input body">
      <select id=${`setting-${l}`} value=${c[l]} onChange=${m=>r(l,m.target.value)}>
        ${v.map(m=>s`<option value=${m}>${m}</option>`)}
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
          ${Ks.map(([l,d,v])=>s`<button type="button" role="radio" aria-checked=${e===l} onClick=${()=>r("theme_mode",l)}>
            <${w} name=${d} size=${15} />${v}</button>`)}
        </div>
        ${i("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(l=>s`<${z} kind="warning">${l}<//>`)}
    <//>
    <${I} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${et} options=${n.figure_styles} value=${c.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${l=>r("figure_style",l)} />`:s`<span class="muted small"><code>${JSON.stringify(c.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(c.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${I} label="keyboard">
      <table class="kv">${lt.map(([l,d])=>s`<tr><td><kbd class="small">${l}</kbd></td><td>${d}</td></tr>`)}</table>
    <//>
    <${I} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(l=>s`
          <tr><td class="muted">${l.name}</td><td><code class="code">${l.logdir}</code> (${l.kind}, ${l.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var Vn={system:"light",light:"dark",dark:"system"},Us={system:"monitor",light:"sun",dark:"moon"};function Wn(){let e=N(he),t=N(pe),n=N(Q);return s`<header class="topbar">
    <${W} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Q.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>ee.set("")} aria-label="Search (⌘K)">
      <${w} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Fs} />
      <${W} icon=${Us[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${Vn[t]})`}
        onClick=${()=>{St("theme_mode",Vn[t])}} />
      <a class="icon-button" href=${We(q.value.page==="group"?q.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${w} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${w} name="settings" size=${16} /></a>
    </div>
  </header>`}function Fs(){let t=(x(ce()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${C(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${w} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${w} name="server" size=${15} /> local</span>`}function js(e){let[t,n]=y(Date.now());return M(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function Gs(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function qn(){let e=N(Ut),t=N(ne),n=N(Ft),a=N(q),o=js(5e3),r=x(Bn()).data,c=P(x(rt()).data),i=N(he),l=r?.daemon,d=r?.runs?.running??0,v=c.filter(E=>E["run.status"]==="failed"&&Gs(E["run.ended_at"])>Un).length,m=r?.meta?.freshness,[p,h,g]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&l?["",`live \xB7 updated ${F(new Date(n).toISOString(),o)}`,`beamtime serve, pid ${l.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${g}><span class=${`live-dot ${p}`}></span>${h}</span>
    ${d?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>ee.set("running")}>
          <${w} name="circle-dot" size=${14} class="tone-accent" />${d} running</button>`:null}
    ${v?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>ee.set("failed")}>
          <${w} name="circle-x" size=${14} />${v} failed since your last visit</button>`:null}
    ${m?.behind?s`<span class="status-item warn-text" data-tip=${m.text}><${w} name="hourglass" size=${14} />${m.behind} runs behind</span>`:null}
    ${m?.damaged?.length?s`<span class="status-item warn-text" data-tip=${m.damaged.join(`
`)}><${w} name="triangle-alert" size=${14} />${m.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${w} name="activity" size=${14} />1 run selected</span>`:null}
    <${W} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ne.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var Xn=null;function dt(e){let t=O(null),[n,a]=y(null),[o,r]=y(!1),[c,i]=y(!1);M(()=>{let m=!0;return Xn??=import("./chunks/md-SW3VT2BQ.js"),Xn.then(p=>p.render(e.text??"")).then(p=>m&&a(p)),()=>{m=!1}},[e.text]),Bt(()=>{let m=t.current;if(!m||!e.clamp)return;let p=()=>i(m.scrollHeight>m.clientHeight+2),h=new ResizeObserver(p);return h.observe(m),()=>h.disconnect()},[e.clamp,n]);let l=e.clamp&&!o,d=`md${l?" clamped":""}`,v=l?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${d} ref=${t} style=${v}>
          ${(e.text??"").split(/\n{2,}/).map(m=>s`<p>${m}</p>`)}
        </div>`:s`<div class=${d} ref=${t} style=${v} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(c||o)?s`<button type="button" class="link small more" onClick=${()=>r(!o)}>${o?"less":"more"}</button>`:null}
  </div>`}function ye(e){let[t,n]=y(!!e.startEditing),[a,o]=y(e.value),[r,c]=y(null),[i,l]=y(null),d=O(null),v=O(!1);M(()=>c(null),[e.value]),M(()=>{!t||!d.current||(d.current.focus(),e.startEditing?d.current.select():d.current.setSelectionRange(d.current.value.length,d.current.value.length))},[t]);let[m,p]=y(!1),h=e.locked??void 0,g=$=>{if(!$.target.closest("a, button, input, summary")){if(h)return p(!0);$.preventDefault(),o(r??e.value),l(null),v.current=!1,n(!0)}},E=()=>{v.current=!0,n(!1),l(null),e.onCancel?.()},f=async()=>{if(v.current)return;v.current=!0;let $=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if($===e.value.trim()||!$&&!e.multiline)return E();n(!1),c($);try{await e.onSave($)}catch(b){c(null),o($),l(b.message),v.current=!1,n(!0)}},k=$=>{if($.key==="Escape")return $.preventDefault(),$.stopPropagation(),E();$.key!=="Enter"||$.isComposing||$.keyCode===229||(!e.multiline||$.metaKey||$.ctrlKey)&&($.preventDefault(),f())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${d} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${$=>o($.target.value)} onKeyDown=${k} onBlur=${f}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let u=r??e.value;return s`<div class=${`editable${h?" locked":""}${r!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${h?`${e.label}: ${h}`:`Edit ${e.label}`}
      data-tip=${h} onClick=${g} onBlur=${()=>p(!1)}
      onKeyDown=${$=>$.key==="Enter"&&$.target===$.currentTarget&&g($)}>
    ${u.trim()?e.render?e.render(u):u:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${m&&h?s`<span class="edit-hint small locked-why" role="status"><${w} name="lock" size=${14} /> ${h}</span>`:null}
  </div>`}function Ct(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${j(e.ci[0])}, ${j(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${j(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${j(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function Et(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function Yn({node:e}){let t=Z("proposal"),n=Z("check"),a=t.data,o=n.data;if(!a)return s`<${ae} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let r=a.proposal??{},c=(a.versions??[]).filter(l=>l.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${ae} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${r.statement}</p>`}
    ${r.rationale?s`<p class="rationale prose">${r.rationale}</p>`:null}
    <div class="predictions">
      ${(o?.predictions??[]).map(l=>s`<div class="prediction" key=${l.name}>
          <${L} spec=${T("result",l.result)} />
          <span class="pname">${l.name}</span>
          <span class="pdetail num small">${Ct(l)}</span>
        </div>`)}
    </div>
    ${c.length?s`<${gt} summary=${`${c.length} earlier version${c.length>1?"s":""}`}>
          ${c.map(l=>s`<p class="small"><code>${l.version}</code> ${l.statement}
            <span class="muted">(${l.runs} runs, check ${l.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function Jn({node:e}){let t=Z("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],o=a.find(i=>i.group===n)??null,r=a.filter(i=>i.group!==n),c=o?.notes_since?"out of date":o?`version ${o.versions??1}`:"none yet";return s`<${Be} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?c:void 0} open=${!1} result=${t}
      action=${s`<${L} spec=${{icon:"circle-help",tone:"muted",label:Ws}} />`}>
    <${ye} value=${o?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${dt} text=${i} />`} onSave=${i=>Mn(n,i)} />
    ${o&&(o.body?.length>(t.data?.budget??1/0)||o.notes_since>=Vs)?s`<p class="memory-meta small warn-text">${o.body?.length>t.data.budget?`${o.body.length} characters, beyond the budget of ${t.data.budget}`:`${o.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${o?s`<p class="memory-meta small">${o.author} · covers notes until ${o.covers_until?.slice(0,10)}
          ${o.notes_since?s` · <span class="warn-text">${o.notes_since} newer note${o.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${r.length?s`<p class="memory-meta small">Memory above this group: ${r.map((i,l)=>s`${l?", ":""}<a href=${C(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var Vs=5,Ws="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",qs="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function Zn({node:e}){let t=Z("main"),n=e.data?.main.params.from??".",a=P(t.data).filter(o=>o.path!==n);return s`<${ae} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(o=>{let[r,c]=Et(o.progress),i=(o.failed??0)+(o.killed??0)+(o.lost??0);return s`<a class="group-row" key=${o.path} href=${C(o.path)}
            onPointerEnter=${()=>je(o.path)} onFocus=${()=>je(o.path)}>
          <${L} spec=${T("research",o.status)} />
          <span class="gname heading">${o.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${o.status!=="concluded"?s`<span class=${`tone-${T("research",o.status).tone}`}>${T("research",o.status).label}</span>`:null}
            ${o.check?s`<${L} spec=${T("result",o.check)} word />`:null}
            ${o.verdict?s`<${L} spec=${T("verdict",o.verdict)} />`:null}
            ${r?s`<span data-tip=${c}>${r}</span>`:null}
            <span class="num"><b>${o.runs}</b> runs</span>
            ${o.running?s`<${L} spec=${T("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${w} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${o.proposal?s`<span class="gstatement caption">${o.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Qn({node:e}){let t=Z("main"),n=e.data?.main.params.from??".",[a,o]=y(!1),r=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),c=t.data?.meta?.matched??r.length;return s`<${Be} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(c):void 0} result=${t}
      action=${s`<${L} spec=${{icon:"circle-help",tone:"muted",label:qs}} />
        ${s`<${W} icon="plus" label="Add a note" onClick=${()=>o(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${Js} group=${n} onDone=${()=>o(!1)} />`:null}
      ${t.data&&!r.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${r.map(i=>s`<${ut} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${es} call=${e.data.main} before=${r[r.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Xs=20;function es(e){let[t,n]=y(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Xs}}:null,o=x(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(o.status==="error")return s`<p class="bad-text small">${o.error}</p>`;let r=o.data?.entries??[];return s`${o.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${r.map(c=>s`<${ut} key=${c.id} note=${c} scope=${e.scope} />`)}
    ${o.data?.more?s`<${es} call=${e.call} before=${r[r.length-1]?.id} scope=${e.scope} />`:null}`}var Ys=["observation","decision","idea","question","theory"];function ts(e){return(e?.note_types??Ys).filter(t=>t!=="verdict")}function Js(e){let t=ts(N(he)),[n,a]=y("observation"),[o,r]=y(""),[c,i]=y(""),[l,d]=y(null),[v,m]=y(!1),p=async g=>{if(g.preventDefault(),!o.trim())return d("give the note a title");m(!0);try{await Tn(e.group,n,o.trim(),c.trim()),e.onDone()}catch(E){d(E.message),m(!1)}};return s`<form class="note new-note" onSubmit=${p} onKeyDown=${g=>{g.key==="Escape"&&e.onDone(),g.key==="Enter"&&(g.metaKey||g.ctrlKey)&&p(g)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${g=>a(g.target.value)}>
        ${t.map(g=>s`<option value=${g}>${g}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${o} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${g=>r(g.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${c} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${g=>i(g.target.value)}></textarea></span>
    <div class="save-actions">
      <${oe} type="submit" icon=${v?"hourglass":"plus"} disabled=${v}>${v?"Adding\u2026":"Add note"}<//>
      <${oe} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${l?s`<span class="bad-text small">${l}</span>`:null}
    </div>
  </form>`}function Zs({note:e}){let t=ts(N(he)).filter(n=>n!==e.type);return e.type==="verdict"?s`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${w} name=${T("note","verdict").icon} size=${15} /></span>`:s`<${Qe} icon=${T("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>s`<button type="button" key=${n} onClick=${()=>st(e,{type:n})}>
        <${w} name=${T("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function ut(e){let t=e.note,[n,a]=y(!!e.open),[o,r]=y(!1),c=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),l=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${d=>!d.target.closest(".editable, a, .note-delete, .popover-wrap")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${w} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${Zs} note=${t} />
      <${ye} value=${t.description} label="the note's title" class="note-title heading" render=${ea}
        onSave=${d=>st(t,{description:d})} />
      ${t.overall?s`<${L} spec=${T("verdict",t.overall)} />`:null}
      ${t.state?s`<${nn} tone="warn">${t.state}<//>`:null}
      ${c?s`<a class="note-group small" href=${C(c)} data-tip="from this group">${Qs(c,e.scope)}</a>`:null}
      <span class="note-meta small">${l?`${l} \xB7 `:""}${F(i)}</span>
      ${s`<${W} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${o}
        onClick=${d=>{d.stopPropagation(),r(!o)}} />`}
    </div>
    ${o?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${oe} icon="trash" kind="danger" onClick=${()=>{Dn(t)}}>Delete<//>
          <${oe} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${ye} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${d=>s`<${dt} text=${d} />`}
          onSave=${d=>st(t,{body:d})} />`:null}
  </article>`}function Qs(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return se(a)?a.slice(-8):n}function ns({node:e}){let t=Z("main"),n=t.data?.lines??[],a=t.data?.meta??{},o=s`<${w} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${ae} result=${t}>
    <${gt} summary=${o} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function ss({node:e}){let t=J(U);return s`<${ae} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ye} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Me.value===e.id} onCancel=${()=>Me.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${dt} text=${n} />`}
      onSave=${n=>(Me.set(null),at(t.path,e.id,n))} />
  <//>`}function as({node:e}){return s`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function ea(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[o]=a.split(/[#@]/),r=o.split("/").pop()??"";return s`<a href=${se(r)?ue(r):C(o)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function os(e){let t=()=>_(C(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${w} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${W} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${ta} id=${e.run} scope=${e.path} />`:s`<${na} path=${e.path} />`}
  </aside>`}function ta({id:e,scope:t}){let n=x(De(e,t)).data,a=x(On(e,t)).data,o=x(Fe(t)).data,r=x({method:"keys",params:{from:t},scope:t}).data,c=le(),i=_e(()=>Je(P(o).map(m=>m["run.id"]),c).get(e),[o,c,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let l=n.run,d=Object.entries(n.metrics??{}),v=Xt(i,c);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${v.class} style=${v.style}></span>
      <a href=${ue(e)}>${l.name}</a></h3>
    <p class="facts small">
      <${L} spec=${T("run",l.status)} word />
      <span><b>${xe(l.steps)}</b> steps</span>
      <span><b>${Se(l.duration_s)}</b></span>
      <span data-tip=${l.created_at}>${F(l.created_at)}</span>
    </p>
    ${l.error?s`<pre class="log code bad-text">${l.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <${nt} config=${n.config??{}} varying=${Ue(r)} />
    ${d.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${d.map(([m,p])=>s`<tr><td>${m}</td><td class="num"><b>${j(p.last)}</b></td>
              <td class="num">${j(p.min)}</td><td class="num">${j(p.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(m=>s`<p class="small"><${L} spec=${T("note",m.type)} /> ${m.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(m=>s`<div class="event small"><span class="muted num">${m.t?.slice(5,16).replace("T"," ")}</span>
        <${w} name=${bt(m.type)} size=${14} /><span>${m.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function na({path:e}){let t=x(ot(e)).data,n=x(zn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${ut} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${w} name=${a.kind==="note"?"file-text":bt(a.type)} size=${14} />
        <span>${a.run?s`<a href=${ue(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var Tt=["failed","killed","lost"];function Mt(e){let t=ke(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=V(e.path)?[]:n.split("/"),o=a.length&&se(a[a.length-1])?a[a.length-1]:null,r=a.slice(0,-1),c=i=>[...t==="."?[]:[t],...r.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${C(t)}>${t==="."?"local":t}</a>`:null}
      ${r.map((i,l)=>s`<span>/</span><a href=${C(c(l))}>${i}</a>`)}
    </nav>
    ${o?s`<${oa} id=${o} scope=${e.path} />`:s`<${sa} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function sa({path:e}){let t=P(x(Ne(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=Tt.reduce((o,r)=>o+(t[r]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${L} spec=${T("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${Tt.filter(o=>t[o]).map(o=>`${t[o]} ${o}`).join(", ")}>
            <${w} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?Tt.find(o=>t[o]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${is} path=${e} />
    </p>`}function rs({path:e}){let t=P(x(Ne(e)).data)[0]??null,n=x(t?.proposal?Rn(e):null).data,a=x(t?.proposal?In(e):null).data;if(!t?.proposal)return null;let o=a?.proposal?.rationale,r=a?.versions?.find(l=>l.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[c,i]=Et(n?.progress?.text??t.progress);return s`<${I} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ye} value=${t.proposal} label="the proposal's statement" locked=${a?r:"Loading the proposal\u2026"}
          render=${l=>s`<span data-tip=${r?void 0:o}>${l}</span>`}
          onSave=${l=>Nn(e,l)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(l=>{let d=T("result",l.result),v=Ct(l),m=v?`${d.label}: ${v}`:d.label;return s`<span class=${`check small tone-${d.tone}`} key=${l.name} data-tip=${m}
              aria-label=${`${l.name}: ${m}`} tabindex="0"><${w} name=${d.icon} size=${14} />${l.name}</span>`})}
        ${n?.provisional||c?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${c?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${c}</span>`:null}
            </span>`:null}
      </div>
      <${aa} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function aa(e){let t=x(e.verdict?ot(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=T("verdict",e.verdict),a=(t?.entries??[]).find(r=>r.type==="verdict"&&(r.group??e.path)===e.path),o=a?be(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${w} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${o}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${o?` \xB7 ${F(o)}`:""}</span>`:null}
  </p>`}function oa({id:e,scope:t}){let n=x(De(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,o=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${ye} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${r=>Pn(a.id,t,r.trim())} />
      <${L} spec=${T("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${xe(a.steps)}</b> steps</span>
      <span><b>${Se(a.duration_s)}</b></span>
      ${n.progress?s`<${ra} run=${a} progress=${n.progress} />`:null}
      <span data-tip=${a.created_at}>${F(a.created_at)}</span>
      <${is} path=${t} />
      <${W} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${o} />
      <${Qe} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${ia(a).map(([r,c])=>s`<tr><td class="muted">${r}</td><td>${c}</td></tr>`)}</table>
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
          ${n.proposals.map(r=>{let c=T("result",r.check);return s`<a class=${`check small tone-${c.tone}`} href=${C(r.group)} data-tip=${r.statement}>
              <${w} name=${c.icon} size=${14} />${r.group==="."?"own proposal":r.group}
              ${r.verdict?s`<${L} spec=${T("verdict",r.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function ra({run:e,progress:t}){let{epoch:n,total:a,fraction:o,steps_per_epoch:r}=t,c=e.status==="running"&&o!==null&&r&&e.steps_per_s?Se((1-o)*a*r/e.steps_per_s):null;return s`<span>epoch <b>${n}</b>${a?` of ${a}`:""}${o===null?"":` \xB7 ${Math.round(o*100)} % through`}${c?` \xB7 about ${c} left`:""}</span>`}function is({path:e}){let t=te(e).main,n=x(kt(e,t)).data?.summary;if(!n)return null;let a=Object.entries(n.config??{}).map(([c,i])=>`${vt(c)} ${j(i)}`).join(", "),o=se(e.split("/").pop()??""),r=`${n.stat} of ${n.metric} over ${o?"the run":"all runs"}${a?` (${a})`:""}`;return s`<span data-tip=${r}>
    best <b>${n.label??vt(`metric.${n.metric}.${n.stat}`)} ${j(n.value)}</b>
    ${o?null:s` · <a href=${ue(n.run)}>${n.name}</a>`}
  </span>`}function ia(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var Nt=80;function ls({node:e}){let t=Z("main"),n=Z(e.data?.keys?"keys":""),a=e.props.mode==="run",o=e.props.title??(a?"Config":"Hyperparameters");return s`<${Be} id=${`config:${e.id}`} title=${o} open=${e.props.open} result=${t}>
    ${t.data?a?s`<${nt} config=${t.data.config} varying=${Ue(n.data)} />`:s`<${la} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function la({rows:e}){let t=new Set(Ue({config:{rows:e}})),n=e.filter(([a])=>t.has(a.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([a,,o])=>{let r=Array.isArray(o)?o.map(j).join(", "):`${j(o.min)} \u2026 ${j(o.max)} \xB7 ${o.distinct} values`;return s`<tr><td data-tip=${a}>${a.replace(/^config\./,"")}</td>
      <td data-tip=${r.length>Nt?r:void 0}>${r.length>Nt?`${r.slice(0,Nt-1)}\u2026`:r}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var cs=15e3;function ds({node:e}){let t=J(U),n=le(),[a,o]=Qt(),r=e.props.code,c=x(o&&r?{method:"code",params:r,scope:null}:null),[i,l]=y(null),[d,v]=y(120),[m,p]=y({error:null,warnings:[]}),h=k=>{me&&console.error(`[block ${e.id}] ${k}`),p(u=>({...u,error:k}))},g=O(()=>{});M(()=>{if(!i)return;let k=!0;Le.n++;let u=()=>{k&&Le.n--,k=!1};g.current=u;let $=setTimeout(()=>{k&&h(`no first render within ${cs/1e3} s`),u()},cs);return()=>{clearTimeout($),u()}},[i]),M(()=>{let k=i?.contentWindow;if(!k||c.status!=="ready")return;let u=D=>k.postMessage(D,"*"),$=new Map,b=new pn,H=D=>{if(D.source!==k)return;let S=D.data;switch(S.type){case"hello":u({type:"init",init:{id:e.id,code:c.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:Zt.value,pair:Xe.value,colormaps:qe.value,prefs:He(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!dn.has(S.call.method)){u({type:"result",id:S.id,result:{status:"error",data:null,error:`${S.call.method} is not available in a custom block`,refreshing:!1}});break}$.get(S.id)?.(),$.set(S.id,Kt(S.call,ie=>u({type:"result",id:S.id,result:ie})));break;case"unsub":$.get(S.id)?.(),$.delete(S.id);break;case"navigate":S.url.startsWith("/")&&_(S.url);break;case"height":b.accept(performance.now())?v(Math.max(40,S.height)):B("its height keeps changing, so it is fixed at its last height");break;case"ready":p(ie=>({...ie,blank:S.blank,overflow:S.overflow})),g.current();break;case"warn":B(S.message);break;case"hover":ft.set(S.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(S.prefs)&&A.set(S.prefs);break;case"download":case"snapshot":S.href?un(S.href,S.name)?performance.now()-G>1e3&&(G=performance.now(),ze().download(S.href,S.name)):B(`a download of ${S.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":ze().figure(S.spec,S.name).catch(ie=>B(`the PDF failed: ${ie.message}`));break;case"expand":mn(S.node)&&ze().expand(S.node,t);break;case"error":h(S.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,E)),g.current();break;default:break}},B=D=>{me&&console.warn(`[block ${e.id}] ${D}`),p(S=>S.warnings.includes(D)?S:{...S,warnings:[...S.warnings,D]})},G=-1/0,A=He(t.path),Y=ft.subscribe(D=>u({type:"hover",run:D})),R=A.subscribe(D=>u({type:"prefs",prefs:D}));return addEventListener("message",H),u({type:"ping"}),()=>{Y(),R(),removeEventListener("message",H);for(let D of $.values())D()}},[c.status,c.data?.code,i]),M(()=>{let k={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(k,"*")},[t.names,t.colors,t.metrics,i]),M(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let E=typeof r=="object"?r.path??r.block:String(r??"");en(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let f=o&&c.status==="ready"&&!m.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${f?s`<span class="chart-tools">
            <${W} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${W} icon="x" label="Close (Esc)" onClick=${()=>Oe.set(null)} />`:s`<${W} icon="maximize" label="Expand" onClick=${()=>ze().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${ae} caption=${e.props.expanded?void 0:e.props.caption} result=${c}>
      ${m.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${E})</span>
            <pre class="code">${m.error}</pre>
          </div>`:null}
      ${m.warnings.map(k=>s`<${z} kind="warning">${k}<//>`)}
      ${f?s`<div class="custom-frame" data-frame-blank=${m.blank?"1":void 0} data-frame-overflow=${m.overflow?"1":void 0}>
            <iframe key=${c.data.code} ref=${l} sandbox="allow-scripts" ...${ca()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${d}px`} />
          </div>`:null}
    <//>
  </div>`}function ca(){if(!!1)return{src:At("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function us({node:e}){let t=Z("main"),n=J(U),a=t.data?.entries??[];return s`<${ae} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(o=>s`<figure key=${`${o.run}/${o.path}`}>
          <img src=${Ht(Re(o.run,n.path),o.path)} alt=${o.caption??e.props.title} loading=${Ie?"eager":"lazy"} />
          <figcaption class="small">step ${xe(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function ms({node:e}){let t=Z("main"),n=t.data?.entries??[];return s`<${ae} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${z}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${xe(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function ps({node:e}){let n=`section.${J(U).path}:${e.id}`,[a,o]=y(()=>Ie||ge(n,e.props.open!==!1)),r=()=>{ve(n,!a),o(!a)},c=s`${(e.children??[]).map(d=>s`<${re} key=${d.id} node=${d} />`)}`,i=J(Ze);if(!e.props.title)return s`<div class="stack">${c}</div>`;let l=i===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${a} aria-label=${l?`${a?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${l?`${a?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${r}>
      <${w} name=${a?"chevron-down":"chevron-right"} size=${16} />${l?null:e.props.title}
    </button>
    ${a?s`<div class="stack">${c}</div>`:null}
  </div>`}function $s({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${re} key=${n.id} node=${n} />`)}
  </div>`}function Pt({node:e,after:t}){let n=J(U),a=te(n.path),o=e.props.min_width??320,r=e.props.columns,c=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${o}px, 100%), 1fr))`,i=e.children??[],l=i.filter(m=>a.removed.includes(m.id)).map(m=>m.id),d=cn(i.filter(m=>!l.includes(m.id)),a.order[e.id]),v=(m,p)=>{let h=d.map(g=>g.id).filter(g=>g!==m);if(h.splice(h.indexOf(p),0,m),rn(n.path,e.id,h),e.id===sn){let g=f=>i.find(k=>k.id===f)?.data?.main?.params?.y?.[0],E=h.map(f=>n.pins.find(k=>k.y===g(f))).filter(f=>!!f);on(n.path,[...E,...n.pins.filter(f=>!E.includes(f))])}};return s`<div class="grid" style=${c}>
    ${d.map(m=>s`<${da} key=${m.id} node=${m} path=${n.path} span=${a.spans[m.id]??m.props.span??1}
      columns=${r} onDrop=${p=>p!==m.id&&v(p,m.id)} />`)}
    ${t??null}
    ${l.length?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ke(n.path,l)}>${l.length} hidden · show</button></div>`:null}
  </div>`}var Dt=[1,2,"full"];function da(e){let[t,n]=y(!1),a=Dt[(Dt.indexOf(e.span)+1)%Dt.length],o=r=>r==="full"?"full width":`${r} column${r===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${r=>{r.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${r=>{r.preventDefault(),n(!1),e.onDrop(r.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${r=>r.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${w} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${o(e.span)}; click for ${o(a)}`}
        aria-label=${`Width ${o(e.span)}`} onClick=${()=>ln(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${re} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function _t({root:e}){let t=J(U),n=te(t.path),a=x({method:"keys",params:{from:t.path},scope:t.path}).data,o=e.props.template;if(!o||!1)return null;let r=new Set(n.removed),c=new Set([...t.charted].filter(([h])=>!r.has(h)).flatMap(([,h])=>h)),i=n.added.filter(h=>!c.has(h)).map(h=>({block:"line",id:`added-${h}`,props:{y:h},data:{main:{...o,params:{...o.params,y:[h]}}}})),l=new Set([...c,...i.filter(h=>!r.has(h.id)).map(h=>h.props.y)]),d=(a?.metrics?.rows??[]).map(h=>h[0]).filter(h=>!l.has(h));if(!a||!(d.length||i.length))return null;let v=h=>[...t.charted].find(([g,E])=>r.has(g)&&E.includes(h))?.[0]??i.find(g=>r.has(g.id)&&g.props.y===h)?.id,m=h=>{let g=v(h);g?Ke(t.path,[g]):tt(t.path,E=>({added:[...E.added,h]}))},p=d.length?s`<div class="add-chart">
        <span class="add-chart-label"><${w} name="plus" size=${16} /> Add a chart</span>
        <${et} single options=${d} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([h])=>m(h)} />
      </div>`:null;return s`<${I}><${Pt} node=${{block:"grid",id:"added",props:{},children:i}} after=${p} /><//>`}function fs({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,o]=y(()=>t.find(i=>i.id===n())?.id??t[0]?.id),r=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),o(i)},c=t.find(i=>i.id===a)??t[0];return Ie?s`<div class="stack">${t.map(i=>s`<${re} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===c?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>r(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${c?s`<div class="stack" role="tabpanel" id=${`panel-${c.id}`} aria-labelledby=${`tab-${c.id}`}>
          ${(c.children??[]).map(i=>s`<${re} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var hs={section:ps,row:$s,grid:Pt,line:yn,table:Cn,stat:Sn,images:us,text:ms,proposal:Yn,note:as,output:ns,config:ls,memory:Jn,groups:Zn,notes:Qn,tabs:fs,scatter:wn,bar:kn,histogram:xn,data_table:hn,timeline:gn,custom:ds,markdown:ss},ua=new Set(["line","scatter","bar","histogram"]);function re({node:e}){return ua.has(e.block)?s`<${ma} node=${e} />`:s`<${yt} node=${e} blocks=${hs} />`}function ma({node:e}){let t=J(U);return te(t.path).removed.includes(e.id)?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ke(t.path,[e.id])}>1 hidden · show</button></div>`:s`<${yt} node=${e} blocks=${hs} />`}function gs(e,t){let n=e.split(`
`),a=t.split(`
`),o=n.length,r=a.length,c=Array.from({length:o+1},()=>new Uint32Array(r+1));for(let v=o-1;v>=0;v--)for(let m=r-1;m>=0;m--)c[v][m]=n[v]===a[m]?c[v+1][m+1]+1:Math.max(c[v+1][m],c[v][m+1]);let i=[],l=0,d=0;for(;l<o&&d<r;)n[l]===a[d]?(i.push({kind:"same",text:n[l]}),l++,d++):c[l+1][d]>=c[l][d+1]?i.push({kind:"removed",text:n[l++]}):i.push({kind:"added",text:a[d++]});for(;l<o;)i.push({kind:"removed",text:n[l++]});for(;d<r;)i.push({kind:"added",text:a[d++]});return i}function vs(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let o=a;for(;o<e.length&&e[o].kind==="same";)o++;let r=a===0?0:t,c=o===e.length?0:t;o-a>r+c+1?n.push(...e.slice(a,a+r),{kind:"skip",count:o-a-r-c},...e.slice(o-c,o)):n.push(...e.slice(a,o)),a=o}return n}var Lt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function bs(e){if(Lt[e.block])return Lt[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(o=>Lt[o.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function mt(e){let t=x(Fe(e.path)),n=le(),a=P(t.data),o=_e(()=>Je(a.map(p=>p["run.id"]),n),[t.data,n]),r=_e(()=>new Map(a.map(p=>[p["run.id"],p["run.name"]??p["run.id"]])),[t.data]),c=te(e.path),i=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${i}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${I} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let l=e.view.view,d={path:e.path,colors:o,names:r,metrics:e.view.metrics??{},charted:Rt(l),pins:c.main??e.view.pins??[]};if(e.plain)return s`<div class=${i}><${U.Provider} value=${d}><${re} node=${l} /><//></div>`;let v=l.block==="section"&&!l.props.title?l.children??[]:[l],m=v.map(p=>Rt(p).size>0).lastIndexOf(!0);return s`<div class=${i}>${e.before}
    <${U.Provider} value=${d}>
      ${v.map((p,h)=>{let g=bs(p);return s`<${I} key=${p.id} label=${g}><${Ze.Provider} value=${g}><${re} node=${p} /><//><//>
          ${h===m?s`<${_t} root=${l} />`:null}`})}
      ${m===-1?s`<${_t} root=${l} />`:null}
    <//>
  </div>`}function Rt(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])Rt(n,t);return t}function ys(e){if(null)return s`<div class="view-source small"><${w} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=N(q),a=n.page==="group"&&n.version,o=t.versions?s`<a href=${C(e.path,{history:!0})}><${w} name="history" size=${14} /> history (${t.versions})</a>`:null,r;switch(t.source){case"draft":r=s`draft <b>${t.draft}</b>`;break;case"view":r=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${F(be(t.version))} by ${t.author??"unknown"}`;break;default:r=s`the built-in view`}return s`<div class="view-source small">
    <${w} name="layout" size=${14} /><span>${r}</span>
    ${a?s`<a href=${C(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!a?s`<${pa} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${$a} path=${e.path} />
        <${fa} path=${e.path} view=${t} />`}
  </div>`}function pa(e){let[t,n]=y(null),a=e.outdated.map(r=>r.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await _n(e.path)}catch(r){n(r.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${w} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function $a(e){let[t,n]=y(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Me.set(await at(e.path,null,""))}catch(o){n(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${w} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function fa(e){let t=te(e.path),n=an(t),[a,o]=y(!1),[r,c]=y(e.view.title??""),[i,l]=y(e.view.finding??""),[d,v]=y(null),[m,p]=y(!1);if(!n&&!a)return null;let h=async g=>{g.preventDefault(),p(!0),v(null);try{let E={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await K("save_view",{path:e.path,prefs:E,title:r,finding:i}),tt(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),Ee(f=>["view","view_history","summary"].includes(f.method)&&f.scope===e.path),o(!1)}catch(E){v(E.message)}finally{p(!1)}};return a?s`<form class="save-form" onSubmit=${h}>
    <${Ae} label="Title"><input value=${r} onInput=${g=>c(g.target.value)} /><//>
    <${Ae} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${g=>l(g.target.value)} /><//>
    <div class="save-actions">
      <${oe} type="submit" icon=${m?"hourglass":"save"} disabled=${m}>${m?"Saving\u2026":"Save as view"}<//>
      <${oe} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
      ${d?s`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:s`<${oe} icon="save" class="save-view" onClick=${()=>o(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function ws(e){let t=x(Hn(e.path)),n=t.data?.entries??[],[a,o]=y(null),r=a??n.slice(0,2).map(i=>i.version).reverse(),c=i=>{let l=r.includes(i)?r.filter(d=>d!==i):[...r,i].slice(-2);o(l.sort())};return t.status==="error"?s`<${z} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${w} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,l)=>s`<li key=${i.version} class=${r.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${r.includes(i.version)} onChange=${()=>c(i.version)} />
            <span class="num muted" data-tip=${i.version}>${F(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${l===0?C(e.path):C(e.path,{version:i.version})}
            onClick=${d=>{d.preventDefault(),_(l===0?C(e.path):C(e.path,{version:i.version}))}}>${l===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${r.length===2?s`<${ha} path=${e.path} a=${r[0]} b=${r[1]} />`:null}
  </section>`}function ha(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=x(t(e.a)).data,a=x(t(e.b)).data,o=x($e(e.path,e.a)).data,r=x($e(e.path,e.b)).data,c=n&&a?vs(gs(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${F(be(e.a))} to ${F(be(e.b))}</h3>
    <pre class="diff code">${c.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${o?.title??e.a}</h3><${mt} path=${e.path} view=${o} plain /></div>
      <div><h3 class="block-title heading">${r?.title??e.b}</h3><${mt} path=${e.path} view=${r} plain /></div>
    </div>
  </div>`}function ks(e){return Kn(e.path),e.history?s`<div class="page"><div class="sections">
      <${I} label=${xs(e.path)}><${Mt} path=${e.path} /><//>
      <${I} label="history"><${ws} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${ga} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function ga(e){let t=te(e.path).main,n=x($e(e.path,e.version,e.draft,t));M(()=>{n.status==="ready"&&requestAnimationFrame(Vt)},[n.status==="ready"]);let a=s`
    <${I} label=${xs(e.path)}>
      <${Mt} path=${e.path} finding=${n.data?.finding} />
      ${n.data?s`<${ys} path=${e.path} view=${n.data} />`:null}
    <//>
    ${se(e.path.split("/").pop()??"")?null:s`<${rs} path=${e.path} />`}`;return n.status==="error"?s`<div class="sections">${a}
      <${I} label="view">
        ${va(e.path,n.error)?s`<${z} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:s`<${z} kind="error">${n.error}<//>`}
      <//>
    </div>`:s`<${mt} path=${e.path} view=${n.data} before=${a} />`}function xs(e){return se(e.split("/").pop()??"")?"run":"group"}function va(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Ss(e){M(()=>{Ce($e(e.id)).then(n=>_(C(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=x($e(e.id));return t.status==="error"?s`<div class="page"><${z} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var ba={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},It=20,Pe=-1,ya=[["day",86400],["week",7*86400],["month",30*86400]];function Es(e){let t=P(x(ce()).data).map(i=>i.path),n=x({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=x({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Ge("Timeline",P(n.data).filter(i=>i["run.status"]==="running").length);let o=Date.now()/1e3,r=P(n.data).filter(i=>i["run.created_at"]).map((i,l)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:o,lane:l})),c=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(be(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${I} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Ae} label="Group" inline>
          <select value=${e.from} onChange=${i=>_(We(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${r.length} runs · ${c.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${I} label="runs">
      ${n.status==="error"?s`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${wa} bars=${r} marks=${c} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function wa(e){let t=le(),n=O(null),a=[...e.bars.flatMap(f=>[f.start,f.end]),...e.marks.map(f=>f.t)],o=a.length?Cs(Math.min(...a),Math.max(...a)):Cs(Date.now()/1e3-86400,Date.now()/1e3),[r,c]=y(o),i=e.bars.length,l=Math.min(900,Math.max(160,(i+1.5)*It+40)),v=vn(n,bn,t?(f=>{let k=$n(r[0],r[1]),u=b=>f.colors[ba[b]??"muted"],$=b=>f.colors[b==="verdict"?"good":b==="decision"?"accent":b==="question"?"warn":"muted"];return{style:Jt(f),height:l,x:{range:r,log:!1,format:b=>fn(b,k.step),label:"",splits:k.at},y:{range:[Pe-.8,i+.5],log:!1,reverse:!0,label:"",size:150,splits:i<=40?[Pe,...e.bars.map(b=>b.lane)]:[Pe],format:b=>b===Pe?"notes":Ea(e.bars[Math.round(b)]?.name??"")},draw:({ctx:b,x:H,y:B,px:G,focused:A})=>{let Y=It*.62*G;for(let R of e.bars){let D=H(R.start),S=Math.max(3*G,H(R.end)-D);b.fillStyle=A!==null&&A!==R.id?Yt(u(R.status),.35):u(R.status),b.beginPath(),b.roundRect(D,B(R.lane)-Y/2,S,Y,3*G),b.fill()}for(let R of e.marks){let D=H(R.t),S=B(Pe),ie=(A===R.id?6:4.5)*G;b.fillStyle=$(R.type),b.beginPath(),b.moveTo(D,S-ie),b.lineTo(D+ie,S),b.lineTo(D,S+ie),b.lineTo(D-ie,S),b.closePath(),b.fill()}},hit:(b,H,B,G)=>{if(Math.abs(H-G(Pe))<It/2){let R=Ca(e.marks,D=>Math.abs(B(D.t)-b),8);return R?{key:R.id,rows:xa(R)}:null}let A=Math.round((H-G(0))/(G(1)-G(0))),Y=e.bars.find(R=>R.lane===A&&B(R.start)-3<=b&&b<=Math.max(B(R.end),B(R.start)+3)+3);return Y?{key:Y.id,rows:ka(Y)}:null},onClick:b=>{let H=e.marks.find(B=>B.id===b);H?_(C(H.group,{drawer:!0})):_(ue(b))}}})(t):null,[r,e.bars,e.marks],t),m=f=>{if(!v.current)return;f.preventDefault();let k=v.current.xAt(f.clientX),u=Math.exp(f.deltaY*.0015);c(([$,b])=>Ot([k-(k-$)*u,k+(b-k)*u],o))},p=O(null),h=f=>p.current={x:f.clientX,range:r},g=f=>{if(!p.current||!v.current||!(f.buttons&1))return;let k=(f.clientX-p.current.x)*v.current.xPerPixel(),[u,$]=p.current.range;Math.abs(f.clientX-p.current.x)>3&&c(Ot([u-k,$-k],o))},E=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${ya.map(([f,k])=>s`<button type="button" role="radio" aria-checked=${Math.abs(r[1]-r[0]-k)<1}
          onClick=${()=>c(Ot([E-k,E+k*.02],[Math.min(o[0],E-k),o[1]]))}>last ${f}</button>`)}
      <button type="button" role="radio" aria-checked=${r[0]===o[0]&&r[1]===o[1]} onClick=${()=>c(o)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${l}px`}
      onWheel=${m} onPointerDown=${h} onPointerMove=${g} onPointerUp=${()=>p.current=null}></div>
    <p class="muted small">${Sa(t)}</p>
  </div>`}function ka(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:F(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Se(e.end-e.start),color:null}]}function xa(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:F(new Date(e.t*1e3).toISOString()),color:null}]}function Sa(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Ca(e,t,n){let a=null,o=n;for(let r of e){let c=t(r);c<o&&([a,o]=[r,c])}return a}function Cs(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Ot([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),o=Math.max(n[0],Math.min(e,n[1]-a));return[o,o+a]}function Ea(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function Ts(){let e=N(Oe),t=O(null);if(M(()=>{let o=t.current;if(!o||!e)return;o.showModal();let r=()=>Oe.set(null);return o.addEventListener("close",r),()=>o.removeEventListener("close",r)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${U.Provider} value=${e.view}><${re} node=${n} /><//>
  </dialog>`}function Ms(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let o=a.indexOf(n);if(o>=0)return 100-Math.min(o,50)-a.length/100;let r=0,c=0;for(let i of a)if(i===n[r]?r++:r>0&&c++,r===n.length)return 40-Math.min(c,39);return 0}function Ds(e){let[t,n]=y(e.query),[a,o]=y(0),r=O(null),c=P(x(ce()).data),i=P(x(rt()).data);M(()=>{let u=r.current;u.showModal();let $=()=>ee.set(null);u.addEventListener("close",$);let b=!1,H=A=>{let Y=u.getBoundingClientRect();return A.clientX<Y.left||A.clientX>Y.right||A.clientY<Y.top||A.clientY>Y.bottom},B=A=>b=H(A),G=A=>b&&H(A)&&u.close();return"closedBy"in HTMLDialogElement.prototype||(u.addEventListener("pointerdown",B),u.addEventListener("pointerup",G)),()=>{u.removeEventListener("close",$),u.removeEventListener("pointerdown",B),u.removeEventListener("pointerup",G)}},[]);let l=()=>r.current?.close(),d=u=>()=>_(u),v=q.value,m=v.page==="group"?v.path:".",p=(u,$,b,H)=>({section:"Commands",label:u,detail:$,sym:{icon:b,tone:"muted",label:u},run:H}),g=[...c.map(u=>({section:"Groups",label:u.path==="."?"local":u.path,detail:`${u.runs} runs${u.proposal?` \xB7 ${u.proposal}`:""}`,sym:T("research",u.status),run:d(C(u.path))})),...i.map(u=>({section:"Runs",label:u["run.name"]??u["run.id"],detail:`${u["run.status"]} \xB7 ${u["run.path"]}`,sym:T("run",u["run.status"]),run:d(C(u["run.path"]))})),p("Theme: light","","sun",()=>Ye("light")),p("Theme: dark","","moon",()=>Ye("dark")),p("Theme: follow the system","","monitor",()=>Ye("system")),p("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),p("Show notes and timeline","i","file-text",d(C(m,{drawer:!0}))),p("Show or hide the sidebar","\u2318B","panel-left",()=>Q.set(!Q.value)),p(ne.value?"Resume live updates":"Pause live updates","p",ne.value?"play":"pause",()=>ne.set(!ne.value)),p("Keyboard shortcuts","?","keyboard",()=>fe.set(!0)),p("Settings","","settings",d("/settings/appearance"))].map(u=>({it:u,s:Math.max(Ms(t,u.label),Ms(t,u.detail)*.5)})).filter(u=>u.s>0).sort((u,$)=>$.s-u.s||Ns(u.it.section)-Ns($.it.section)).slice(0,60).map(u=>u.it),E=u=>{u&&(l(),u.run())},f=u=>{if(u.key==="ArrowDown")o(Math.min(g.length-1,a+1));else if(u.key==="ArrowUp")o(Math.max(0,a-1));else if(u.key==="Enter")E(g[a]);else return;u.preventDefault()},k="";return s`<dialog class="sheet" ref=${r} aria-label="Search" closedby="any">
    <div class="palette-input"><${w} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${g[a]?`pal-${a}`:void 0}
        onInput=${u=>{n(u.target.value),o(0)}} onKeyDown=${f} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${g.map((u,$)=>{let b=u.section!==k&&!t?k=u.section:null;return s`${b?s`<li class="palette-head small" role="presentation">${b}</li>`:null}
          <li id=${`pal-${$}`} class="item" role="option" aria-selected=${$===a}
              onMouseMove=${()=>o($)} onClick=${()=>E(u)}>
            <${L} spec=${u.sym} /><span class="label">${u.label}</span><span class="detail small">${u.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function Ns(e){return["Groups","Runs","Commands"].indexOf(e)}function pt(e,t=[]){let n=new Map,a=(i,l={})=>({path:i,name:i==="."?"local":i.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let i of e)n.set(i.path,a(i.path,i));(t.length===0||t.some(i=>i.name==="local"))&&!n.has(".")&&n.set(".",a("."));for(let i of t){let l=i.name==="local"?".":i.name;n.has(l)||n.set(l,a(l)),Object.assign(n.get(l),{state:i.state,error:i.error})}for(let i of n.values()){if(V(i.path))continue;let l=i.path.lastIndexOf("/"),d=l<0?".":i.path.slice(0,l);(n.get(d)??n.get(ke(i.path))??n.get(".")).children.push(i)}for(let i of n.values())i.children.sort((l,d)=>l.name.localeCompare(d.name));let r=[...n.values()].filter(i=>i.path!=="."&&V(i.path)).sort((i,l)=>i.name.localeCompare(l.name)),c=n.get(".");return c?[c,...r]:r}function Ps(e,t,n,a=new Set){let o=[],r=n.toLowerCase(),c=i=>{(!r||i.path.toLowerCase().includes(r)||_s(i,r))&&(o.push(i),(r||(V(i.path)?!a.has(i.path):t.has(i.path)))&&i.children.forEach(c))};return e.forEach(c),o}function _s(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||_s(n,t))}function Ls(e,t){if(V(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),o=r=>r.path===a?r:r.children.map(o).find(c=>c)??null;return e.map(o).find(r=>r)?.children??[]}function Rs(e){return V(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Is(){let e=N(q),t=x(ce()),[n,a]=y(()=>new Set(ge("open",[]))),[o,r]=y(()=>new Set(ge("closed-hosts",[]))),[c,i]=y(""),l=O(null),d=e.page==="group"?e.path:null,v=pt(P(t.data),t.data?.meta?.sources??[]),m=Ps(v,Na(n,d),c,o),p=f=>V(f)?!o.has(f):n.has(f),h=(f,k)=>{let u=k??!p(f);if(V(f)){let b=new Set(o);u?b.delete(f):b.add(f),ve("closed-hosts",[...b]),r(b);return}let $=new Set(n);u?$.add(f):$.delete(f),ve("open",[...$]),a($)},g=O(d);return M(()=>{d!==g.current&&d&&!V(d)&&o.has(ke(d))&&h(ke(d),!0),g.current=d},[d]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${w} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${c} aria-label="Filter groups"
        onInput=${f=>i(f.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${f=>{let k=[...l.current?.querySelectorAll("a.tree-item")??[]],u=k.indexOf(document.activeElement),$=m[u];switch(f.key){case"ArrowDown":k[Math.min(k.length-1,u+1)]?.focus();break;case"ArrowUp":k[Math.max(0,u-1)]?.focus();break;case"ArrowRight":$?.children.length&&h($.path,!0);break;case"ArrowLeft":$?.children.length&&p($.path)?h($.path,!1):$&&k[m.findIndex(b=>b.path===Ma($.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${m.map(f=>s`<${Ta} key=${f.path} node=${f} current=${f.path===d}
        open=${p(f.path)||!!c} onToggle=${()=>h(f.path)} />`)}
    </div>
  </nav>`}function Ta(e){let t=e.node,n=()=>je(t.path),a=t.children.length>0,o=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${V(t.path)?" source-root":""}`} href=${C(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${8+Rs(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${r=>{r.metaKey||r.ctrlKey||(r.preventDefault(),_(C(t.path)))}}>
    <span class="twisty" onClick=${r=>{r.preventDefault(),r.stopPropagation(),e.onToggle()}}>
      ${a?s`<${w} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${V(t.path)?s`<${L} size=${14} spec=${{icon:o?"cloud-off":"server",tone:"muted",label:o?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${L} spec=${T("run","running")} size=${14} />`:null}
      ${t.failed?s`<${L} spec=${{...T("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Ma(e){if(V(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function Na(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let o=1;o<a.length;o++)n.add(a.slice(0,o).join("/"));return n}function zs(){let e=N(q),t=N(Q),n=N(ee),a=N(fe),o=O(null);M(()=>Gt(()=>o.current),[]),M(()=>(addEventListener("keydown",Os),()=>removeEventListener("keydown",Os)),[]);let r=e.page==="group"&&e.drawer,c;switch(e.page){case"group":c=s`<${ks} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":c=s`<${Ss} id=${e.id} />`;break;case"settings":c=s`<${Gn} />`;break;case"timeline":c=s`<${Es} key=${e.from} from=${e.from} />`;break;default:c=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return me||!1?s`<main class="main render-main" ref=${o}>${c}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${r?" with-drawer":""}`}>
    <${Wn} />
    ${t?s`<${Is} />`:null}
    <main class="main" ref=${o}>${c}</main>
    ${r?s`<${os} path=${e.path} run=${e.run} />`:null}
    <${qn} />
    ${n!==null?s`<${Ds} query=${n} />`:null}
    ${a?s`<${Pa} />`:null}
    <${Ts} />
  </div>`}function Os(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),ee.set(ee.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Q.set(!Q.value);return}if(e.key==="Escape"){if(ee.value!==null||fe.value)return;let a=q.value;return a.page==="group"&&a.run?_(C(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?_(C(a.path),{replace:!0}):void 0}if(t||e.altKey||Fn(e)||ee.value!==null||fe.value)return;let n=q.value;switch(e.key){case"/":e.preventDefault(),ee.set("");break;case"?":fe.set(!fe.value);break;case"p":ne.set(!ne.value);break;case"i":n.page==="group"&&_(C(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Q.set(!Q.value);break;case"[":case"]":n.page==="group"&&Da(n.path,e.key==="]"?1:-1);break}}async function Da(e,t){let n=await Ce(ce()),a=Ls(pt(P(n),n?.meta?.sources??[]),e),o=a.findIndex(c=>c.path===e),r=a[o+t];r&&_(C(r.path))}function Pa(){let e=O(null);return M(()=>{let t=e.current;t.showModal();let n=()=>fe.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${lt.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${oe} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Wt();if(me){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(pe.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Le.n,qt&&tn()}En();var _a=K("meta").then(e=>(me&&(e={...e,settings:{...e.settings,theme_mode:pe.value}}),ct(e),e));!me&&!!1&&jt(async()=>{let[e,t]=await Promise.all([_a,K("meta")]);e.bundle!==t.bundle?location.reload():ct(t)});zt(s`<${zs} />`,document.getElementById("app"));
