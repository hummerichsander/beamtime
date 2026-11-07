import{$ as W,A as Yt,Aa as fn,B as me,Ba as hn,C as Ie,Ca as bn,D as Jt,Da as yn,E as Xe,Ea as wn,F as ht,G as pe,Ga as kn,H as tn,Ha as xn,I as gt,Ia as Cn,J as Ye,Ja as Sn,K as U,Ka as En,L as Z,La as Tn,M as le,Ma as Mn,N as Je,Na as Nn,O as nn,P as Oe,Q as ze,S as sn,T as an,U as w,V as _,W as Ze,X as ae,Y as z,Z as P,_ as Be,a,aa as on,ba as O,ca as oe,d as K,da as Ae,e as Le,ea as vt,f as Se,fa as Qe,g as ft,ga as et,h as x,ha as rn,i as jt,ia as He,j as ne,ja as te,k as Gt,ka as tt,l as Vt,la as ln,m as Wt,ma as cn,n as Ee,na as Ke,o as se,oa as dn,p as S,pa as un,q as We,qa as mn,r as ue,ra as M,s as _e,sa as yt,t as ke,ta as Ue,u as V,ua as nt,v as q,va as wt,w as qt,wa as pn,y as R,z as Xt,za as $n}from"./chunks/chunk-G4FXOVAI.js";import{a as Ut,b as Ft}from"./chunks/chunk-O2K4N3UR.js";import{B as Qt,C as en,D as j,G as be,H as xe,I as Ce,J as F,K as bt,V as gn,W as vn,b as At,d as Ht,f as y,g as T,h as Kt,i as L,j as Re,k as J,n as we,o as N,p as ge,q as ve,v as Zt,x as qe}from"./chunks/chunk-VBF3SWAC.js";import"./chunks/chunk-VC46IEJQ.js";function Te(e,t){Ee(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var kt=["notes","timeline","groups","check","card","memory_show","status"];async function st(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Te(e.group,kt)}async function Dn(e,t,n,s){await K("note_add",{group:e,type:t,description:n,body:s}),Te(e,kt)}async function Pn(e,t){await K("memory_update",{group:e,body:t}),Te(e,["memory_show","status"])}async function Rn(e,t){let n=await K("proposal_show",{group:e}),s=Object.fromEntries(Object.entries(n.proposal??{}).filter(([o])=>!["schema","author","user","supersedes"].includes(o)));await K("proposal_set",{group:e,proposal:{...s,statement:t}}),Te(e,["groups","proposal_show","check","summary"])}async function Ln(e){await K("note_rm",{note:e.id}),Te(e.group,kt)}async function _n(e,t,n){await K("name",{run:e,name:n}),Te(t,["card","runs","groups","summary","series"])}async function at(e,t,n){let s=await K("view_text",{path:e,id:t,text:n});return Ee(o=>["view","view_history"].includes(o.method)&&o.scope===e),s.id}async function In(e){await K("view_upgrade",{group:e}),Ee(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Me=new we(null);async function On(e,t){return await K("set",{key:e,value:t}),K("meta")}var ce=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),$e=(e,t=null,n=null,s=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...s?{metrics:s}:{}},scope:e}),xt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),Ne=e=>({method:"groups",params:{from:e,depth:0},scope:e}),zn=e=>({method:"check",params:{group:e},scope:e}),Bn=e=>({method:"proposal_show",params:{group:e},scope:e}),De=(e,t)=>({method:"card",params:{run:_e(e,t)},scope:t}),An=(e,t)=>({method:"output",params:{run:_e(e,t),tail:30},scope:t}),Fe=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),ot=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Hn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Kn=()=>({method:"status",params:{},scope:"."}),rt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function je(e){let t=He(e).value.main;for(let n of[$e(e,null,null,t),Ne(e),Fe(e),xt(e,t)])ft(n);Se($e(e,null,null,t)).then(n=>{for(let s of Un(n.view))ft(s)}).catch(()=>{})}function Un(e){return e?[...Us.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(Un)]:[]}var Us=new Set(["line","custom"]),Fn=e=>({method:"view_history",params:{group:e},scope:e});var Ct="/static/favicon.svg",it=null;async function Fs(){if(it)return it;let e=new Image;e.src=Ct,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let s=n.getContext("2d");if(!s)return Ct;s.drawImage(e,0,0,t,t),s.beginPath(),s.arc(t-6,t-6,6,0,Math.PI*2);let o=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return s.fillStyle=o||"#2f5aa8",s.fill(),it=n.toDataURL("image/png"),it}function js(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=Ct;return}Fs().then(n=>{t.type="image/png",t.href=n})}}function Ge(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,js(t>0)},[e,t])}function jn(e){let t=se(e.split("/").pop()??""),n=x(t?null:Ne(e)),s=x(t?De(e.split("/").pop()??"",e):null),o=t?s.data?.run.name??s.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,r=t?s.data?.run.status==="running"?1:0:P(n.data)[0]?.running??0;Ge(o,r)}var Q=new we(ge("sidebar",!0)),ee=new we(null),fe=new we(!1),he=new we(null);Q.subscribe(e=>ve("sidebar",e));var Gn=ge("visit",Date.now());ve("visit",Date.now());function Vn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var lt=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Gs=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function ct(e){he.set(e),Xe.set(e.theme),qe.set(e.colormaps),e.settings?.theme_mode&&pe.set(e.settings.theme_mode),gt()}var Wn=0;async function St(e,t){let n=++Wn;e==="theme_mode"&&(pe.set(t),gt());let s=await On(e,t);n===Wn&&ct(s)}function qn(){let e=N(pe),t=le(),n=N(he),[s,o]=y(null);Ge("Settings");let r=(l,d)=>{o(null),St(l,d).catch(v=>o(v.message))},c=n?.settings??{},i=(l,d,v)=>a`
    <label class="field-label small" for=${`setting-${l}`}>${d}</label>
    <span class="input body">
      <select id=${`setting-${l}`} value=${c[l]} onChange=${m=>r(l,m.target.value)}>
        ${v.map(m=>a`<option value=${m}>${m}</option>`)}
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
          ${Gs.map(([l,d,v])=>a`<button type="button" role="radio" aria-checked=${e===l} onClick=${()=>r("theme_mode",l)}>
            <${w} name=${d} size=${15} />${v}</button>`)}
        </div>
        ${i("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(l=>a`<${z} kind="warning">${l}<//>`)}
    <//>
    <${O} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?a`<${et} options=${n.figure_styles} value=${c.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${l=>r("figure_style",l)} />`:a`<span class="muted small"><code>${JSON.stringify(c.figure_style??[])}</code>; choosing others needs the figures
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
  </div></div>`}var Xn={system:"light",light:"dark",dark:"system"},Vs={system:"monitor",light:"sun",dark:"moon"};function Yn(){let e=N(he),t=N(pe),n=N(Q);return a`<header class="topbar">
    <${W} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Q.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>ee.set("")} aria-label="Search (⌘K)">
      <${w} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Ws} />
      <${W} icon=${Vs[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${Xn[t]})`}
        onClick=${()=>{St("theme_mode",Xn[t])}} />
      <a class="icon-button" href=${We(q.value.page==="group"?q.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${w} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${w} name="settings" size=${16} /></a>
    </div>
  </header>`}function Ws(){let t=(x(ce()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?a`${[{name:"local",state:"connected"},...t].map(n=>a`<a class=${`source small ${n.state}`}
      href=${S(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${w} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:a`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${w} name="server" size=${15} /> local</span>`}function qs(e){let[t,n]=y(Date.now());return T(()=>{let s=setInterval(()=>n(Date.now()),e);return()=>clearInterval(s)},[e]),t}function Xs(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function Jn(){let e=N(Gt),t=N(ne),n=N(Vt),s=N(q),o=qs(5e3),r=x(Kn()).data,c=P(x(rt()).data),i=N(he),l=r?.daemon,d=r?.runs?.running??0,v=c.filter(E=>E["run.status"]==="failed"&&Xs(E["run.ended_at"])>Gn).length,m=r?.meta?.freshness,[p,h,g]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&l?["",`live \xB7 updated ${F(new Date(n).toISOString(),o)}`,`beamtime serve, pid ${l.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return a`<footer class="statusbar small">
    <span class="status-item" data-tip=${g}><span class=${`live-dot ${p}`}></span>${h}</span>
    ${d?a`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>ee.set("running")}>
          <${w} name="circle-dot" size=${14} class="tone-accent" />${d} running</button>`:null}
    ${v?a`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>ee.set("failed")}>
          <${w} name="circle-x" size=${14} />${v} failed since your last visit</button>`:null}
    ${m?.behind?a`<span class="status-item warn-text" data-tip=${m.text}><${w} name="hourglass" size=${14} />${m.behind} runs behind</span>`:null}
    ${m?.damaged?.length?a`<span class="status-item warn-text" data-tip=${m.damaged.join(`
`)}><${w} name="triangle-alert" size=${14} />${m.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${s.page==="group"&&s.run?a`<span class="status-item"><${w} name="activity" size=${14} />1 run selected</span>`:null}
    <${W} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ne.set(!t)} />
    ${i?.outdated?a`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var Zn=null;function dt(e){let t=L(null),[n,s]=y(null),[o,r]=y(!1),[c,i]=y(!1);T(()=>{let m=!0;return Zn??=import("./chunks/md-SW3VT2BQ.js"),Zn.then(p=>p.render(e.text??"")).then(p=>m&&s(p)),()=>{m=!1}},[e.text]),Kt(()=>{let m=t.current;if(!m||!e.clamp)return;let p=()=>i(m.scrollHeight>m.clientHeight+2),h=new ResizeObserver(p);return h.observe(m),()=>h.disconnect()},[e.clamp,n]);let l=e.clamp&&!o,d=`md${l?" clamped":""}`,v=l?`--clamp:${e.clamp}`:"";return a`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?a`<div class=${d} ref=${t} style=${v}>
          ${(e.text??"").split(/\n{2,}/).map(m=>a`<p>${m}</p>`)}
        </div>`:a`<div class=${d} ref=${t} style=${v} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(c||o)?a`<button type="button" class="link small more" onClick=${()=>r(!o)}>${o?"less":"more"}</button>`:null}
  </div>`}function ye(e){let[t,n]=y(!!e.startEditing),[s,o]=y(e.value),[r,c]=y(null),[i,l]=y(null),d=L(null),v=L(!1);T(()=>c(null),[e.value]),T(()=>{!t||!d.current||(d.current.focus(),e.startEditing?d.current.select():d.current.setSelectionRange(d.current.value.length,d.current.value.length))},[t]);let[m,p]=y(!1),h=e.locked??void 0,g=$=>{if(!$.target.closest("a, button, input, summary")){if(h)return p(!0);$.preventDefault(),o(r??e.value),l(null),v.current=!1,n(!0)}},E=()=>{v.current=!0,n(!1),l(null),e.onCancel?.()},f=async()=>{if(v.current)return;v.current=!0;let $=e.multiline?s.trim():s.replace(/\s*\n\s*/g," ").trim();if($===e.value.trim()||!$&&!e.multiline)return E();n(!1),c($);try{await e.onSave($)}catch(b){c(null),o($),l(b.message),v.current=!1,n(!0)}},k=$=>{if($.key==="Escape")return $.preventDefault(),$.stopPropagation(),E();$.key!=="Enter"||$.isComposing||$.keyCode===229||(!e.multiline||$.metaKey||$.ctrlKey)&&($.preventDefault(),f())};if(t)return a`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${d} class="edit-field" value=${s} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,s.split(`
`).length+1)):1}
        onInput=${$=>o($.target.value)} onKeyDown=${k} onBlur=${f}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?a` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let u=r??e.value;return a`<div class=${`editable${h?" locked":""}${r!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${h?`${e.label}: ${h}`:`Edit ${e.label}`}
      data-tip=${h} onClick=${g} onBlur=${()=>p(!1)}
      onKeyDown=${$=>$.key==="Enter"&&$.target===$.currentTarget&&g($)}>
    ${u.trim()?e.render?e.render(u):u:a`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${m&&h?a`<span class="edit-hint small locked-why" role="status"><${w} name="lock" size=${14} /> ${h}</span>`:null}
  </div>`}function Et(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${j(e.ci[0])}, ${j(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${j(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${j(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function Tt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function Qn({node:e}){let t=Z("proposal"),n=Z("check"),s=t.data,o=n.data;if(!s)return a`<${ae} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let r=s.proposal??{},c=(s.versions??[]).filter(l=>l.version!==s.version),i=!e.props.of||e.props.of===".";return a`<${ae} title="Predictions" result=${t} class="proposal">
    ${i?null:a`<p class="statement">${r.statement}</p>`}
    ${r.rationale?a`<p class="rationale prose">${r.rationale}</p>`:null}
    <div class="predictions">
      ${(o?.predictions??[]).map(l=>a`<div class="prediction" key=${l.name}>
          <${_} spec=${M("result",l.result)} />
          <span class="pname">${l.name}</span>
          <span class="pdetail num small">${Et(l)}</span>
        </div>`)}
    </div>
    ${c.length?a`<${vt} summary=${`${c.length} earlier version${c.length>1?"s":""}`}>
          ${c.map(l=>a`<p class="small"><code>${l.version}</code> ${l.statement}
            <span class="muted">(${l.runs} runs, check ${l.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function es({node:e}){let t=Z("main"),n=e.data?.main.params.group??".",s=t.data?.chain??[],o=s.find(i=>i.group===n)??null,r=s.filter(i=>i.group!==n),c=o?.notes_since?"out of date":o?`version ${o.versions??1}`:"none yet";return a`<${Be} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?c:void 0} open=${!1} result=${t}
      action=${a`<${_} spec=${{icon:"circle-help",tone:"muted",label:Js}} />`}>
    <${ye} value=${o?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>a`<${dt} text=${i} />`} onSave=${i=>Pn(n,i)} />
    ${o&&(o.body?.length>(t.data?.budget??1/0)||o.notes_since>=Ys)?a`<p class="memory-meta small warn-text">${o.body?.length>t.data.budget?`${o.body.length} characters, beyond the budget of ${t.data.budget}`:`${o.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${o?a`<p class="memory-meta small">${o.author} · covers notes until ${o.covers_until?.slice(0,10)}
          ${o.notes_since?a` · <span class="warn-text">${o.notes_since} newer note${o.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${r.length?a`<p class="memory-meta small">Memory above this group: ${r.map((i,l)=>a`${l?", ":""}<a href=${S(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var Ys=5,Js="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Zs="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function ts({node:e}){let t=Z("main"),n=e.data?.main.params.from??".",s=P(t.data).filter(o=>o.path!==n);return a`<${ae} title=${e.props.title} count=${t.data?String(s.length):void 0} result=${t}>
    ${t.data&&!s.length?a`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${s.map(o=>{let[r,c]=Tt(o.progress),i=(o.failed??0)+(o.killed??0)+(o.lost??0);return a`<a class="group-row" key=${o.path} href=${S(o.path)}
            onPointerEnter=${()=>je(o.path)} onFocus=${()=>je(o.path)}>
          <${_} spec=${M("research",o.status)} />
          <span class="gname heading">${o.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${o.status!=="concluded"?a`<span class=${`tone-${M("research",o.status).tone}`}>${M("research",o.status).label}</span>`:null}
            ${o.check?a`<${_} spec=${M("result",o.check)} word />`:null}
            ${o.verdict?a`<${_} spec=${M("verdict",o.verdict)} />`:null}
            ${r?a`<span data-tip=${c}>${r}</span>`:null}
            <span class="num"><b>${o.runs}</b> runs</span>
            ${o.running?a`<${_} spec=${M("run","running")} />`:null}
            ${i?a`<span class="tone-bad num" data-tip="failed, killed or lost"><${w} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${o.proposal?a`<span class="gstatement caption">${o.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function ns({node:e}){let t=Z("main"),n=e.data?.main.params.from??".",[s,o]=y(!1),r=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),c=t.data?.meta?.matched??r.length;return a`<${Be} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(c):void 0} result=${t}
      action=${a`<${_} spec=${{icon:"circle-help",tone:"muted",label:Zs}} />
        ${a`<${W} icon="plus" label="Add a note" onClick=${()=>o(!0)} />`}`}>
    <div class="notes">
      ${s?a`<${ta} group=${n} onDone=${()=>o(!1)} />`:null}
      ${t.data&&!r.length&&!s?a`<p class="muted small">No notes yet.</p>`:null}
      ${r.map(i=>a`<${ut} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?a`<${ss} call=${e.data.main} before=${r[r.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Qs=20;function ss(e){let[t,n]=y(!1),s=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Qs}}:null,o=x(s);if(!t)return a`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(o.status==="error")return a`<p class="bad-text small">${o.error}</p>`;let r=o.data?.entries??[];return a`${o.data?null:a`<div class="skeleton" style="block-size: 40px"></div>`}
    ${r.map(c=>a`<${ut} key=${c.id} note=${c} scope=${e.scope} />`)}
    ${o.data?.more?a`<${ss} call=${e.call} before=${r[r.length-1]?.id} scope=${e.scope} />`:null}`}var ea=["observation","decision","idea","question","theory"];function as(e){return(e?.note_types??ea).filter(t=>t!=="verdict")}function ta(e){let t=as(N(he)),[n,s]=y("observation"),[o,r]=y(""),[c,i]=y(""),[l,d]=y(null),[v,m]=y(!1),p=async g=>{if(g.preventDefault(),!o.trim())return d("give the note a title");m(!0);try{await Dn(e.group,n,o.trim(),c.trim()),e.onDone()}catch(E){d(E.message),m(!1)}};return a`<form class="note new-note" onSubmit=${p} onKeyDown=${g=>{g.key==="Escape"&&e.onDone(),g.key==="Enter"&&(g.metaKey||g.ctrlKey)&&p(g)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${g=>s(g.target.value)}>
        ${t.map(g=>a`<option value=${g}>${g}</option>`)}
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
      ${l?a`<span class="bad-text small">${l}</span>`:null}
    </div>
  </form>`}function na({note:e}){let t=as(N(he)).filter(n=>n!==e.type);return e.type==="verdict"?a`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${w} name=${M("note","verdict").icon} size=${15} /></span>`:a`<${Qe} icon=${M("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>a`<button type="button" key=${n} onClick=${()=>st(e,{type:n})}>
        <${w} name=${M("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function ut(e){let t=e.note,[n,s]=y(!!e.open),[o,r]=y(!1),c=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),l=t.meta?.author;return a`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${d=>!d.target.closest(".editable, a, .note-delete, .popover-wrap")&&s(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${w} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${na} note=${t} />
      <${ye} value=${t.description} label="the note's title" class="note-title heading" render=${aa}
        onSave=${d=>st(t,{description:d})} />
      ${t.overall?a`<${_} spec=${M("verdict",t.overall)} />`:null}
      ${t.state?a`<${on} tone="warn">${t.state}<//>`:null}
      ${c?a`<a class="note-group small" href=${S(c)} data-tip="from this group">${sa(c,e.scope)}</a>`:null}
      <span class="note-meta small">${l?`${l} \xB7 `:""}${F(i)}</span>
      ${a`<${W} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${o}
        onClick=${d=>{d.stopPropagation(),r(!o)}} />`}
    </div>
    ${o?a`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${oe} icon="trash" kind="danger" onClick=${()=>{Ln(t)}}>Delete<//>
          <${oe} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
        </div>`:null}
    ${n?a`<${ye} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${d=>a`<${dt} text=${d} />`}
          onSave=${d=>st(t,{body:d})} />`:null}
  </article>`}function sa(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,s=n.split("/").pop()??n;return se(s)?s.slice(-8):n}function os({node:e}){let t=Z("main"),n=t.data?.lines??[],s=t.data?.meta??{},o=a`<${w} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${s.total_lines??n.length} lines${(s.shown??0)<(s.total_lines??0)?`, last ${s.shown}`:""}`:""}</span>`;return a`<${ae} result=${t}>
    <${vt} summary=${o} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function rs({node:e}){let t=J(U);return a`<${ae} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ye} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Me.value===e.id} onCancel=${()=>Me.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>a`<${dt} text=${n} />`}
      onSave=${n=>(Me.set(null),at(t.path,e.id,n))} />
  <//>`}function is({node:e}){return a`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function aa(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let s=n.slice(2,-2),[o]=s.split(/[#@]/),r=o.split("/").pop()??"";return a`<a href=${se(r)?ue(r):S(o)}>${s}</a>`}return n.startsWith("`")?a`<code>${n.slice(1,-1)}</code>`:n})}function ls(e){let t=()=>R(S(e.path),{replace:!0});return a`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${w} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${W} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?a`<${oa} id=${e.run} scope=${e.path} />`:a`<${ra} path=${e.path} />`}
  </aside>`}function oa({id:e,scope:t}){let n=x(De(e,t)).data,s=x(An(e,t)).data,o=x(Fe(t)).data,r=x({method:"keys",params:{from:t},scope:t}).data,c=le(),i=Re(()=>Je(P(o).map(m=>m["run.id"]),c).get(e),[o,c,e]);if(!n)return a`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let l=n.run,d=Object.entries(n.metrics??{}),v=Zt(i,c);return a`<div class="drawer-body">
    <h3 class="heading"><span class=${v.class} style=${v.style}></span>
      <a href=${ue(e)}>${l.name}</a></h3>
    <p class="facts small">
      <${_} spec=${M("run",l.status)} word />
      <span><b>${xe(l.steps)}</b> steps</span>
      <span><b>${Ce(l.duration_s)}</b></span>
      <span data-tip=${l.created_at}>${F(l.created_at)}</span>
    </p>
    ${l.error?a`<pre class="log code bad-text">${l.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <${nt} config=${n.config??{}} varying=${Ue(r)} />
    ${d.length?a`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${d.map(([m,p])=>a`<tr><td>${m}</td><td class="num"><b>${j(p.last)}</b></td>
              <td class="num">${j(p.min)}</td><td class="num">${j(p.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?a`<h4 class="small">Cited by</h4>${n.cited_by.map(m=>a`<p class="small"><${_} spec=${M("note",m.type)} /> ${m.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(m=>a`<div class="event small"><span class="muted num">${m.t?.slice(5,16).replace("T"," ")}</span>
        <${w} name=${yt(m.type)} size=${14} /><span>${m.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(s?.lines??[]).join(`
`)}</pre>
  </div>`}function ra({path:e}){let t=x(ot(e)).data,n=x(Hn(e)).data;return a`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?a`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(s=>!String(s.state??"").startsWith("superseded")).map(s=>a`<${ut} key=${s.id} note=${s} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(s=>a`<div class="event small"><span class="muted num">${s.t?.slice(5,16).replace("T"," ")}</span>
        <${w} name=${s.kind==="note"?"file-text":yt(s.type)} size=${14} />
        <span>${s.run?a`<a href=${ue(s.run)}>${s.run.slice(-8)}</a> `:null}${s.description??s.type}</span></div>`)}
  </div>`}function mt(e,t){let n=x(e),s=L(null);return n.status!=="loading"&&(s.current={scope:t,result:n}),n.status==="loading"&&s.current?.scope===t?s.current.result:n}var Mt=null;function cs(e){Mt?.();let t=document.querySelector(".main");if(!e||!t)return;let n=e.getBoundingClientRect().top,s=new ResizeObserver(()=>{e.isConnected&&(t.scrollTop+=e.getBoundingClientRect().top-n)});for(let i of t.children)s.observe(i);let o=["wheel","touchmove","keydown","pointerdown"],r=()=>{s.disconnect(),clearTimeout(c);for(let i of o)removeEventListener(i,r);Mt=null},c=setTimeout(r,5e3);for(let i of o)addEventListener(i,r,{passive:!0});Mt=r}var Nt=["failed","killed","lost"];function Dt(e){let t=ke(e.path),n=t==="."?e.path:e.path.slice(t.length+1),s=V(e.path)?[]:n.split("/"),o=s.length&&se(s[s.length-1])?s[s.length-1]:null,r=s.slice(0,-1),c=i=>[...t==="."?[]:[t],...r.slice(0,i+1)].join("/");return a`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${s.length?a`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${r.map((i,l)=>a`<span>/</span><a href=${S(c(l))}>${i}</a>`)}
    </nav>
    ${o?a`<${ca} id=${o} scope=${e.path} />`:a`<${ia} path=${e.path} />`}
    ${e.finding?a`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function ia({path:e}){let t=P(x(Ne(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return a`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=Nt.reduce((o,r)=>o+(t[r]??0),0);return a`
    <h1 class="page-title title" tabindex="-1">${n} <${_} spec=${M("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?a`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?a`<span><b>${t.finished}</b> finished</span>`:null}
      ${s?a`<span class="tone-bad" data-tip=${Nt.filter(o=>t[o]).map(o=>`${t[o]} ${o}`).join(", ")}>
            <${w} name="circle-x" size=${15} /> <b>${s}</b> ${s===1?Nt.find(o=>t[o]):"ended early"}</span>`:null}
      ${t.notes?a`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${us} path=${e} />
    </p>`}function ds({path:e}){let t=P(x(Ne(e)).data)[0]??null,n=x(t?.proposal?zn(e):null).data,s=x(t?.proposal?Bn(e):null).data;if(!t?.proposal)return null;let o=s?.proposal?.rationale,r=s?.versions?.find(l=>l.version===s.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[c,i]=Tt(n?.progress?.text??t.progress);return a`<${O} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ye} value=${t.proposal} label="the proposal's statement" locked=${s?r:"Loading the proposal\u2026"}
          render=${l=>a`<span data-tip=${r?void 0:o}>${l}</span>`}
          onSave=${l=>Rn(e,l)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(l=>{let d=M("result",l.result),v=Et(l),m=v?`${d.label}: ${v}`:d.label;return a`<span class=${`check small tone-${d.tone}`} key=${l.name} data-tip=${m}
              aria-label=${`${l.name}: ${m}`} tabindex="0"><${w} name=${d.icon} size=${14} />${l.name}</span>`})}
        ${n?.provisional||c?a`<span class="small">
              ${n?.provisional?a`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${c?a`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${c}</span>`:null}
            </span>`:null}
      </div>
      <${la} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function la(e){let t=x(e.verdict?ot(e.path):null).data;if(!e.verdict)return a`<p class="verdict-line muted">no verdict yet</p>`;let n=M("verdict",e.verdict),s=(t?.entries??[]).find(r=>r.type==="verdict"&&(r.group??e.path)===e.path),o=s?be(s.id):null;return a`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${w} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${s?a`<span class="small muted" data-tip=${o}>verdict${s.meta?.author?` by ${s.meta.author}`:""}${o?` \xB7 ${F(o)}`:""}</span>`:null}
  </p>`}function ca({id:e,scope:t}){let n=x(De(e,t)).data;if(!n)return a`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=n.run,o=()=>{navigator.clipboard?.writeText(s.id)};return a`
    <h1 class="page-title title" tabindex="-1"><${ye} value=${s.name??s.id} label="the run's name" class="title-edit"
        onSave=${r=>_n(s.id,t,r.trim())} />
      <${_} spec=${M("run",s.status)} word /></h1>
    ${s.error?a`<p class="bad-text" data-tip=${s.error}>${s.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${xe(s.steps)}</b> steps</span>
      <span><b>${Ce(s.duration_s)}</b></span>
      ${n.progress?a`<${da} run=${s} progress=${n.progress} />`:null}
      <span data-tip=${s.created_at}>${F(s.created_at)}</span>
      <${us} path=${t} />
      <${W} icon="copy" label=${`Copy the run id ${s.id}`} onClick=${o} />
      <${Qe} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${ua(s).map(([r,c])=>a`<tr><td class="muted">${r}</td><td>${c}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>R(S(t,{run:s.id}),{replace:!0})}>
            <${w} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${o}><${w} name="copy" size=${15} /> Copy the run id</button>
          ${s.git?.commit?a`<button type="button" onClick=${()=>navigator.clipboard?.writeText(s.git.commit)}>
            <${w} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?a`<div class="checks">
          ${n.proposals.map(r=>{let c=M("result",r.check);return a`<a class=${`check small tone-${c.tone}`} href=${S(r.group)} data-tip=${r.statement}>
              <${w} name=${c.icon} size=${14} />${r.group==="."?"own proposal":r.group}
              ${r.verdict?a`<${_} spec=${M("verdict",r.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function da({run:e,progress:t}){let{epoch:n,total:s,fraction:o,steps_per_epoch:r}=t,c=e.status==="running"&&o!==null&&r&&e.steps_per_s?Ce((1-o)*s*r/e.steps_per_s):null;return a`<span>epoch <b>${n}</b>${s?` of ${s}`:""}${o===null?"":` \xB7 ${Math.round(o*100)} % through`}${c?` \xB7 about ${c} left`:""}</span>`}function us({path:e}){let t=te(e).main,n=mt(xt(e,t),e).data?.summary;if(!n)return null;let s=Object.entries(n.config??{}).map(([c,i])=>`${bt(c)} ${j(i)}`).join(", "),o=se(e.split("/").pop()??""),r=`${n.stat} of ${n.metric} over ${o?"the run":"all runs"}${s?` (${s})`:""}`;return a`<span data-tip=${r}>
    best <b>${n.label??bt(`metric.${n.metric}.${n.stat}`)} ${j(n.value)}</b>
    ${o?null:a` · <a href=${ue(n.run)}>${n.name}</a>`}
  </span>`}function ua(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,s])=>[n,String(s)])}var Pt=80;function ms({node:e}){let t=Z("main"),n=Z(e.data?.keys?"keys":""),s=e.props.mode==="run",o=e.props.title??(s?"Config":"Hyperparameters");return a`<${Be} id=${`config:${e.id}`} title=${o} open=${e.props.open} result=${t}>
    ${t.data?s?a`<${nt} config=${t.data.config} varying=${Ue(n.data)} />`:a`<${ma} rows=${t.data.config?.rows??[]} />`:a`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function ma({rows:e}){let t=new Set(Ue({config:{rows:e}})),n=e.filter(([s])=>t.has(s.replace(/^config\./,"")));return n.length?a`<table class="kv small">${n.map(([s,,o])=>{let r=Array.isArray(o)?o.map(j).join(", "):`${j(o.min)} \u2026 ${j(o.max)} \xB7 ${o.distinct} values`;return a`<tr><td data-tip=${s}>${s.replace(/^config\./,"")}</td>
      <td data-tip=${r.length>Pt?r:void 0}>${r.length>Pt?`${r.slice(0,Pt-1)}\u2026`:r}</td></tr>`})}</table>`:a`<p class="muted small">No config differs between the runs.</p>`}var ps=15e3;function $s({node:e}){let t=J(U),n=le(),[s,o]=nn(),r=e.props.code,c=x(o&&r?{method:"code",params:r,scope:null}:null),[i,l]=y(null),[d,v]=y(120),[m,p]=y({error:null,warnings:[]}),h=k=>{me&&console.error(`[block ${e.id}] ${k}`),p(u=>({...u,error:k}))},g=L(()=>{});T(()=>{if(!i)return;let k=!0;Le.n++;let u=()=>{k&&Le.n--,k=!1};g.current=u;let $=setTimeout(()=>{k&&h(`no first render within ${ps/1e3} s`),u()},ps);return()=>{clearTimeout($),u()}},[i]),T(()=>{let k=i?.contentWindow;if(!k||c.status!=="ready")return;let u=D=>k.postMessage(D,"*"),$=new Map,b=new hn,H=D=>{if(D.source!==k)return;let C=D.data;switch(C.type){case"hello":u({type:"init",init:{id:e.id,code:c.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:tn.value,pair:Xe.value,colormaps:qe.value,prefs:He(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!pn.has(C.call.method)){u({type:"result",id:C.id,result:{status:"error",data:null,error:`${C.call.method} is not available in a custom block`,refreshing:!1}});break}$.get(C.id)?.(),$.set(C.id,jt(C.call,ie=>u({type:"result",id:C.id,result:ie})));break;case"unsub":$.get(C.id)?.(),$.delete(C.id);break;case"navigate":C.url.startsWith("/")&&R(C.url);break;case"height":b.accept(performance.now())?v(Math.max(40,C.height)):B("its height keeps changing, so it is fixed at its last height");break;case"ready":p(ie=>({...ie,blank:C.blank,overflow:C.overflow})),g.current();break;case"warn":B(C.message);break;case"hover":ht.set(C.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(C.prefs)&&A.set(C.prefs);break;case"download":case"snapshot":C.href?$n(C.href,C.name)?performance.now()-G>1e3&&(G=performance.now(),ze().download(C.href,C.name)):B(`a download of ${C.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":ze().figure(C.spec,C.name).catch(ie=>B(`the PDF failed: ${ie.message}`));break;case"expand":fn(C.node)&&ze().expand(C.node,t);break;case"error":h(C.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,E)),g.current();break;default:break}},B=D=>{me&&console.warn(`[block ${e.id}] ${D}`),p(C=>C.warnings.includes(D)?C:{...C,warnings:[...C.warnings,D]})},G=-1/0,A=He(t.path),Y=ht.subscribe(D=>u({type:"hover",run:D})),I=A.subscribe(D=>u({type:"prefs",prefs:D}));return addEventListener("message",H),u({type:"ping"}),()=>{Y(),I(),removeEventListener("message",H);for(let D of $.values())D()}},[c.status,c.data?.code,i]),T(()=>{let k={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(k,"*")},[t.names,t.colors,t.metrics,i]),T(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let E=typeof r=="object"?r.path??r.block:String(r??"");sn(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let f=o&&c.status==="ready"&&!m.error;return a`<div ref=${s} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${f?a`<span class="chart-tools">
            <${W} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?a`<${W} icon="x" label="Close (Esc)" onClick=${()=>Oe.set(null)} />`:a`<${W} icon="maximize" label="Expand" onClick=${()=>ze().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${ae} caption=${e.props.expanded?void 0:e.props.caption} result=${c}>
      ${m.error?a`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${E})</span>
            <pre class="code">${m.error}</pre>
          </div>`:null}
      ${m.warnings.map(k=>a`<${z} kind="warning">${k}<//>`)}
      ${f?a`<div class="custom-frame" data-frame-blank=${m.blank?"1":void 0} data-frame-overflow=${m.overflow?"1":void 0}>
            <iframe key=${c.data.code} ref=${l} sandbox="allow-scripts" ...${pa()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${d}px`} />
          </div>`:null}
    <//>
  </div>`}function pa(){if(!!1)return{src:Ut("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function fs({node:e}){let t=Z("main"),n=J(U),s=t.data?.entries??[];return a`<${ae} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!s.length?a`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${s.map(o=>a`<figure key=${`${o.run}/${o.path}`}>
          <img src=${Ft(_e(o.run,n.path),o.path)} alt=${o.caption??e.props.title} loading=${Ie?"eager":"lazy"} />
          <figcaption class="small">step ${xe(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function hs({node:e}){let t=Z("main"),n=t.data?.entries??[];return a`<${ae} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?a`<${z}>No text logged.<//>`:null}
    ${n.map(s=>a`<div class="text-entry" key=${`${s.run}/${s.step}`}>
        <div class="muted small">step ${xe(s.step)}${s.caption?` \xB7 ${s.caption}`:""}</div>
        <pre class="code">${s.text??""}</pre>
      </div>`)}
  <//>`}function gs({node:e}){let n=`section.${J(U).path}:${e.id}`,[s,o]=y(()=>Ie||ge(n,e.props.open!==!1)),r=()=>{ve(n,!s),o(!s)},c=a`${(e.children??[]).map(d=>a`<${re} key=${d.id} node=${d} />`)}`,i=J(Ze);if(!e.props.title)return a`<div class="stack">${c}</div>`;let l=i===e.props.title.toLowerCase();return a`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${s} aria-label=${l?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${l?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${r}>
      <${w} name=${s?"chevron-down":"chevron-right"} size=${16} />${l?null:e.props.title}
    </button>
    ${s?a`<div class="stack">${c}</div>`:null}
  </div>`}function vs({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return a`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>a`<${re} key=${n.id} node=${n} />`)}
  </div>`}function Lt({node:e,after:t}){let n=J(U),s=te(n.path),o=e.props.min_width??320,r=e.props.columns,c=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${o}px, 100%), 1fr))`,i=e.children??[],l=i.filter(m=>s.removed.includes(m.id)).map(m=>m.id),d=mn(i.filter(m=>!l.includes(m.id)),s.order[e.id]),v=(m,p)=>{let h=d.map(g=>g.id).filter(g=>g!==m);if(h.splice(h.indexOf(p),0,m),dn(n.path,e.id,h),e.id===rn){let g=f=>i.find(k=>k.id===f)?.data?.main?.params?.y?.[0],E=h.map(f=>n.pins.find(k=>k.y===g(f))).filter(f=>!!f);cn(n.path,[...E,...n.pins.filter(f=>!E.includes(f))])}};return a`<div class="grid" style=${c}>
    ${d.map(m=>a`<${$a} key=${m.id} node=${m} path=${n.path} span=${s.spans[m.id]??m.props.span??1}
      columns=${r} onDrop=${p=>p!==m.id&&v(p,m.id)} />`)}
    ${t??null}
    ${l.length?a`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ke(n.path,l)}>${l.length} hidden · show</button></div>`:null}
  </div>`}var Rt=[1,2,"full"];function $a(e){let[t,n]=y(!1),s=Rt[(Rt.indexOf(e.span)+1)%Rt.length],o=r=>r==="full"?"full width":`${r} column${r===1?"":"s"}`;return a`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${r=>{r.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${r=>{r.preventDefault(),n(!1),e.onDrop(r.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${r=>r.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${w} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${o(e.span)}; click for ${o(s)}`}
        aria-label=${`Width ${o(e.span)}`} onClick=${()=>un(e.path,e.node.id,s)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${re} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function _t({root:e}){let t=J(U),n=te(t.path),s=x({method:"keys",params:{from:t.path},scope:t.path}).data,o=e.props.template;if(!o||!1)return null;let r=new Set(n.removed),c=new Set([...t.charted].filter(([h])=>!r.has(h)).flatMap(([,h])=>h)),i=n.added.filter(h=>!c.has(h)).map(h=>({block:"line",id:`added-${h}`,props:{y:h},data:{main:{...o,params:{...o.params,y:[h]}}}})),l=new Set([...c,...i.filter(h=>!r.has(h.id)).map(h=>h.props.y)]),d=(s?.metrics?.rows??[]).map(h=>h[0]).filter(h=>!l.has(h));if(!s||!(d.length||i.length))return null;let v=h=>[...t.charted].find(([g,E])=>r.has(g)&&E.includes(h))?.[0]??i.find(g=>r.has(g.id)&&g.props.y===h)?.id,m=h=>{let g=v(h);g?Ke(t.path,[g]):tt(t.path,E=>({added:[...E.added,h]}))},p=d.length?a`<div class="add-chart">
        <span class="add-chart-label"><${w} name="plus" size=${16} /> Add a chart</span>
        <${et} single options=${d} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([h])=>m(h)} />
      </div>`:null;return a`<${O}><${Lt} node=${{block:"grid",id:"added",props:{},children:i}} after=${p} /><//>`}function bs({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[s,o]=y(()=>t.find(i=>i.id===n())?.id??t[0]?.id),r=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),o(i)},c=t.find(i=>i.id===s)??t[0];return Ie?a`<div class="stack">${t.map(i=>a`<${re} key=${i.id} node=${i} />`)}</div>`:a`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>a`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===c?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>r(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${c?a`<div class="stack" role="tabpanel" id=${`panel-${c.id}`} aria-labelledby=${`tab-${c.id}`}>
          ${(c.children??[]).map(i=>a`<${re} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var ys={section:gs,row:vs,grid:Lt,line:xn,table:Mn,stat:Tn,images:fs,text:hs,proposal:Qn,note:is,output:os,config:ms,memory:es,groups:ts,notes:ns,tabs:bs,scatter:Cn,bar:Sn,histogram:En,data_table:bn,timeline:yn,custom:$s,markdown:rs},fa=new Set(["line","scatter","bar","histogram"]);function re({node:e}){return fa.has(e.block)?a`<${ha} node=${e} />`:a`<${wt} node=${e} blocks=${ys} />`}function ha({node:e}){let t=J(U);return te(t.path).removed.includes(e.id)?a`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ke(t.path,[e.id])}>1 hidden · show</button></div>`:a`<${wt} node=${e} blocks=${ys} />`}function ws(e,t){let n=e.split(`
`),s=t.split(`
`),o=n.length,r=s.length,c=Array.from({length:o+1},()=>new Uint32Array(r+1));for(let v=o-1;v>=0;v--)for(let m=r-1;m>=0;m--)c[v][m]=n[v]===s[m]?c[v+1][m+1]+1:Math.max(c[v+1][m],c[v][m+1]);let i=[],l=0,d=0;for(;l<o&&d<r;)n[l]===s[d]?(i.push({kind:"same",text:n[l]}),l++,d++):c[l+1][d]>=c[l][d+1]?i.push({kind:"removed",text:n[l++]}):i.push({kind:"added",text:s[d++]});for(;l<o;)i.push({kind:"removed",text:n[l++]});for(;d<r;)i.push({kind:"added",text:s[d++]});return i}function ks(e,t=3){let n=[],s=0;for(;s<e.length;){if(e[s].kind!=="same"){n.push(e[s++]);continue}let o=s;for(;o<e.length&&e[o].kind==="same";)o++;let r=s===0?0:t,c=o===e.length?0:t;o-s>r+c+1?n.push(...e.slice(s,s+r),{kind:"skip",count:o-s-r-c},...e.slice(o-c,o)):n.push(...e.slice(s,o)),s=o}return n}var It={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function xs(e){if(It[e.block])return It[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(o=>It[o.block])),[s]=n;if(n.size===1&&s)return s}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function pt(e){let t=x(Fe(e.path)),n=le(),s=P(t.data),o=Re(()=>Je(s.map(p=>p["run.id"]),n),[t.data,n]),r=Re(()=>new Map(s.map(p=>[p["run.id"],p["run.name"]??p["run.id"]])),[t.data]),c=te(e.path),i=e.plain?"view plain":"sections view";if(!e.view)return a`<div class=${i}>${e.before}
      ${e.plain?a`<div class="skeleton late" style="block-size: 320px"></div>`:a`<${O} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let l=e.view.view,d={path:e.path,colors:o,names:r,metrics:e.view.metrics??{},charted:Ot(l),pins:c.main??e.view.pins??[]};if(e.plain)return a`<div class=${i}><${U.Provider} value=${d}><${re} node=${l} /><//></div>`;let v=l.block==="section"&&!l.props.title?l.children??[]:[l],m=v.map(p=>Ot(p).size>0).lastIndexOf(!0);return a`<div class=${i}>${e.before}
    <${U.Provider} value=${d}>
      ${v.map((p,h)=>{let g=xs(p);return a`<${At} key=${p.id}><${O} label=${g}><${Ze.Provider} value=${g}><${re} node=${p} /><//><//>
          ${h===m?a`<${_t} root=${l} />`:null}<//>`})}
      ${m===-1?a`<${_t} root=${l} />`:null}
    <//>
  </div>`}function Ot(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])Ot(n,t);return t}function Cs(e){if(null)return a`<div class="view-source small"><${w} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=N(q),s=n.page==="group"&&n.version,o=t.versions?a`<a href=${S(e.path,{history:!0})}><${w} name="history" size=${14} /> history (${t.versions})</a>`:null,r;switch(t.source){case"draft":r=a`draft <b>${t.draft}</b>`;break;case"view":r=a`${t.title?a`<em>${t.title}</em> · `:null}saved ${F(be(t.version))} by ${t.author??"unknown"}`;break;default:r=a`the built-in view`}return a`<div class="view-source small">
    <${w} name="layout" size=${14} /><span>${r}</span>
    ${s?a`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!s?a`<${ga} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||s?null:a`<${va} path=${e.path} />
        <${ba} path=${e.path} view=${t} />`}
  </div>`}function ga(e){let[t,n]=y(null),s=e.outdated.map(r=>r.name).join(", ");return a`<button type="button" class="link small" onClick=${async()=>{n(null);try{await In(e.path)}catch(r){n(r.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${s} exists; update re-pins this view to it (a new version)`}>
      <${w} name="update" size=${14} /> update ${s}</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function va(e){let[t,n]=y(null);return a`<button type="button" class="link small" onClick=${async()=>{n(null);try{Me.set(await at(e.path,null,""))}catch(o){n(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${w} name="file-text" size=${14} /> add text</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function ba(e){let t=te(e.path),n=ln(t),[s,o]=y(!1),[r,c]=y(e.view.title??""),[i,l]=y(e.view.finding??""),[d,v]=y(null),[m,p]=y(!1);if(!n&&!s)return null;let h=async g=>{g.preventDefault(),p(!0),v(null);try{let E={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await K("save_view",{path:e.path,prefs:E,title:r,finding:i}),tt(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),Ee(f=>["view","view_history","summary"].includes(f.method)&&f.scope===e.path),o(!1)}catch(E){v(E.message)}finally{p(!1)}};return s?a`<form class="save-form" onSubmit=${h}>
    <${Ae} label="Title"><input value=${r} onInput=${g=>c(g.target.value)} /><//>
    <${Ae} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${g=>l(g.target.value)} /><//>
    <div class="save-actions">
      <${oe} type="submit" icon=${m?"hourglass":"save"} disabled=${m}>${m?"Saving\u2026":"Save as view"}<//>
      <${oe} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
      ${d?a`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:a`<${oe} icon="save" class="save-view" onClick=${()=>o(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function Ss(e){let t=x(Fn(e.path)),n=t.data?.entries??[],[s,o]=y(null),r=s??n.slice(0,2).map(i=>i.version).reverse(),c=i=>{let l=r.includes(i)?r.filter(d=>d!==i):[...r,i].slice(-2);o(l.sort())};return t.status==="error"?a`<${z} kind="error">${t.error}<//>`:a`<section class="history">
    <h2 class="history-title heading"><${w} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?a`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,l)=>a`<li key=${i.version} class=${r.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${r.includes(i.version)} onChange=${()=>c(i.version)} />
            <span class="num muted" data-tip=${i.version}>${F(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?a`<span>${i.message}</span>`:null}</label>
          <a href=${l===0?S(e.path):S(e.path,{version:i.version})}
            onClick=${d=>{d.preventDefault(),R(l===0?S(e.path):S(e.path,{version:i.version}))}}>${l===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${r.length===2?a`<${ya} path=${e.path} a=${r[0]} b=${r[1]} />`:null}
  </section>`}function ya(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=x(t(e.a)).data,s=x(t(e.b)).data,o=x($e(e.path,e.a)).data,r=x($e(e.path,e.b)).data,c=n&&s?ks(ws(n.yaml,s.yaml)):[];return a`<div class="compare">
    <h3 class="block-title heading">Changes from ${F(be(e.a))} to ${F(be(e.b))}</h3>
    <pre class="diff code">${c.map(i=>i.kind==="skip"?a`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:a`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${o?.title??e.a}</h3><${pt} path=${e.path} view=${o} plain /></div>
      <div><h3 class="block-title heading">${r?.title??e.b}</h3><${pt} path=${e.path} view=${r} plain /></div>
    </div>
  </div>`}function Es(e){return jn(e.path),e.history?a`<div class="page"><div class="sections">
      <${O} label=${Ts(e.path)}><${Dt} path=${e.path} /><//>
      <${O} label="history"><${Ss} path=${e.path} /><//>
    </div></div>`:a`<div class="page">
    <${wa} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function wa(e){let t=te(e.path).main,n=mt($e(e.path,e.version,e.draft,t),`${e.path}|${e.version}|${e.draft}`);T(()=>{n.status==="ready"&&requestAnimationFrame(Xt)},[n.status==="ready"]),T(()=>{let o=r=>cs(r.target.closest?.(".chart-frame")??null);return addEventListener("click",o,!0),()=>removeEventListener("click",o,!0)},[]);let s=a`
    <${O} label=${Ts(e.path)}>
      <${Dt} path=${e.path} finding=${n.data?.finding} />
      ${n.data?a`<${Cs} path=${e.path} view=${n.data} />`:null}
    <//>
    ${se(e.path.split("/").pop()??"")?null:a`<${ds} path=${e.path} />`}`;return n.status==="error"?a`<div class="sections">${s}
      <${O} label="view">
        ${ka(e.path,n.error)?a`<${z} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:a`<${z} kind="error">${n.error}<//>`}
      <//>
    </div>`:a`<${pt} path=${e.path} view=${n.data} before=${s} />`}function Ts(e){return se(e.split("/").pop()??"")?"run":"group"}function ka(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Ms(e){T(()=>{Se($e(e.id)).then(n=>R(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=x($e(e.id));return t.status==="error"?a`<div class="page"><${z} kind="error">${t.error}<//></div>`:a`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var xa={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},zt=20,Pe=-1,Ca=[["day",86400],["week",7*86400],["month",30*86400]];function Ds(e){let t=P(x(ce()).data).map(i=>i.path),n=x({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),s=x({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Ge("Timeline",P(n.data).filter(i=>i["run.status"]==="running").length);let o=Date.now()/1e3,r=P(n.data).filter(i=>i["run.created_at"]).map((i,l)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:o,lane:l})),c=(s.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(be(i.id))/1e3}));return a`<div class="page timeline-page"><div class="sections">
    <${O} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Ae} label="Group" inline>
          <select value=${e.from} onChange=${i=>R(We(i.target.value),{replace:!0})}>
            ${t.map(i=>a`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${r.length} runs · ${c.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${O} label="runs">
      ${n.status==="error"?a`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&s.data?a`<${Sa} bars=${r} marks=${c} />`:a`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function Sa(e){let t=le(),n=L(null),s=[...e.bars.flatMap(f=>[f.start,f.end]),...e.marks.map(f=>f.t)],o=s.length?Ns(Math.min(...s),Math.max(...s)):Ns(Date.now()/1e3-86400,Date.now()/1e3),[r,c]=y(o),i=e.bars.length,l=Math.min(900,Math.max(160,(i+1.5)*zt+40)),v=wn(n,kn,t?(f=>{let k=gn(r[0],r[1]),u=b=>f.colors[xa[b]??"muted"],$=b=>f.colors[b==="verdict"?"good":b==="decision"?"accent":b==="question"?"warn":"muted"];return{style:en(f),height:l,x:{range:r,log:!1,format:b=>vn(b,k.step),label:"",splits:k.at},y:{range:[Pe-.8,i+.5],log:!1,reverse:!0,label:"",size:150,splits:i<=40?[Pe,...e.bars.map(b=>b.lane)]:[Pe],format:b=>b===Pe?"notes":Da(e.bars[Math.round(b)]?.name??"")},draw:({ctx:b,x:H,y:B,px:G,focused:A})=>{let Y=zt*.62*G;for(let I of e.bars){let D=H(I.start),C=Math.max(3*G,H(I.end)-D);b.fillStyle=A!==null&&A!==I.id?Qt(u(I.status),.35):u(I.status),b.beginPath(),b.roundRect(D,B(I.lane)-Y/2,C,Y,3*G),b.fill()}for(let I of e.marks){let D=H(I.t),C=B(Pe),ie=(A===I.id?6:4.5)*G;b.fillStyle=$(I.type),b.beginPath(),b.moveTo(D,C-ie),b.lineTo(D+ie,C),b.lineTo(D,C+ie),b.lineTo(D-ie,C),b.closePath(),b.fill()}},hit:(b,H,B,G)=>{if(Math.abs(H-G(Pe))<zt/2){let I=Na(e.marks,D=>Math.abs(B(D.t)-b),8);return I?{key:I.id,rows:Ta(I)}:null}let A=Math.round((H-G(0))/(G(1)-G(0))),Y=e.bars.find(I=>I.lane===A&&B(I.start)-3<=b&&b<=Math.max(B(I.end),B(I.start)+3)+3);return Y?{key:Y.id,rows:Ea(Y)}:null},onClick:b=>{let H=e.marks.find(B=>B.id===b);H?R(S(H.group,{drawer:!0})):R(ue(b))}}})(t):null,[r,e.bars,e.marks],t),m=f=>{if(!v.current)return;f.preventDefault();let k=v.current.xAt(f.clientX),u=Math.exp(f.deltaY*.0015);c(([$,b])=>Bt([k-(k-$)*u,k+(b-k)*u],o))},p=L(null),h=f=>p.current={x:f.clientX,range:r},g=f=>{if(!p.current||!v.current||!(f.buttons&1))return;let k=(f.clientX-p.current.x)*v.current.xPerPixel(),[u,$]=p.current.range;Math.abs(f.clientX-p.current.x)>3&&c(Bt([u-k,$-k],o))},E=Math.max(...s,Date.now()/1e3);return a`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Ca.map(([f,k])=>a`<button type="button" role="radio" aria-checked=${Math.abs(r[1]-r[0]-k)<1}
          onClick=${()=>c(Bt([E-k,E+k*.02],[Math.min(o[0],E-k),o[1]]))}>last ${f}</button>`)}
      <button type="button" role="radio" aria-checked=${r[0]===o[0]&&r[1]===o[1]} onClick=${()=>c(o)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${l}px`}
      onWheel=${m} onPointerDown=${h} onPointerMove=${g} onPointerUp=${()=>p.current=null}></div>
    <p class="muted small">${Ma(t)}</p>
  </div>`}function Ea(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:F(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Ce(e.end-e.start),color:null}]}function Ta(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:F(new Date(e.t*1e3).toISOString()),color:null}]}function Ma(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Na(e,t,n){let s=null,o=n;for(let r of e){let c=t(r);c<o&&([s,o]=[r,c])}return s}function Ns(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Bt([e,t],n){let s=Math.min(n[1]-n[0],Math.max(60,t-e)),o=Math.max(n[0],Math.min(e,n[1]-s));return[o,o+s]}function Da(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function Ps(){let e=N(Oe),t=L(null);if(T(()=>{let o=t.current;if(!o||!e)return;o.showModal();let r=()=>Oe.set(null);return o.addEventListener("close",r),()=>o.removeEventListener("close",r)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},s=String(n.props.title??n.props.y??"Chart");return a`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${s} closedby="any">
    <${U.Provider} value=${e.view}><${re} node=${n} /><//>
  </dialog>`}function Rs(e,t){let n=e.toLowerCase(),s=t.toLowerCase();if(!n)return 1;let o=s.indexOf(n);if(o>=0)return 100-Math.min(o,50)-s.length/100;let r=0,c=0;for(let i of s)if(i===n[r]?r++:r>0&&c++,r===n.length)return 40-Math.min(c,39);return 0}function _s(e){let[t,n]=y(e.query),[s,o]=y(0),r=L(null),c=P(x(ce()).data),i=P(x(rt()).data);T(()=>{let u=r.current;u.showModal();let $=()=>ee.set(null);u.addEventListener("close",$);let b=!1,H=A=>{let Y=u.getBoundingClientRect();return A.clientX<Y.left||A.clientX>Y.right||A.clientY<Y.top||A.clientY>Y.bottom},B=A=>b=H(A),G=A=>b&&H(A)&&u.close();return"closedBy"in HTMLDialogElement.prototype||(u.addEventListener("pointerdown",B),u.addEventListener("pointerup",G)),()=>{u.removeEventListener("close",$),u.removeEventListener("pointerdown",B),u.removeEventListener("pointerup",G)}},[]);let l=()=>r.current?.close(),d=u=>()=>R(u),v=q.value,m=v.page==="group"?v.path:".",p=(u,$,b,H)=>({section:"Commands",label:u,detail:$,sym:{icon:b,tone:"muted",label:u},run:H}),g=[...c.map(u=>({section:"Groups",label:u.path==="."?"local":u.path,detail:`${u.runs} runs${u.proposal?` \xB7 ${u.proposal}`:""}`,sym:M("research",u.status),run:d(S(u.path))})),...i.map(u=>({section:"Runs",label:u["run.name"]??u["run.id"],detail:`${u["run.status"]} \xB7 ${u["run.path"]}`,sym:M("run",u["run.status"]),run:d(S(u["run.path"]))})),p("Theme: light","","sun",()=>Ye("light")),p("Theme: dark","","moon",()=>Ye("dark")),p("Theme: follow the system","","monitor",()=>Ye("system")),p("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),p("Show notes and timeline","i","file-text",d(S(m,{drawer:!0}))),p("Show or hide the sidebar","\u2318B","panel-left",()=>Q.set(!Q.value)),p(ne.value?"Resume live updates":"Pause live updates","p",ne.value?"play":"pause",()=>ne.set(!ne.value)),p("Keyboard shortcuts","?","keyboard",()=>fe.set(!0)),p("Settings","","settings",d("/settings/appearance"))].map(u=>({it:u,s:Math.max(Rs(t,u.label),Rs(t,u.detail)*.5)})).filter(u=>u.s>0).sort((u,$)=>$.s-u.s||Ls(u.it.section)-Ls($.it.section)).slice(0,60).map(u=>u.it),E=u=>{u&&(l(),u.run())},f=u=>{if(u.key==="ArrowDown")o(Math.min(g.length-1,s+1));else if(u.key==="ArrowUp")o(Math.max(0,s-1));else if(u.key==="Enter")E(g[s]);else return;u.preventDefault()},k="";return a`<dialog class="sheet" ref=${r} aria-label="Search" closedby="any">
    <div class="palette-input"><${w} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${g[s]?`pal-${s}`:void 0}
        onInput=${u=>{n(u.target.value),o(0)}} onKeyDown=${f} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${g.map((u,$)=>{let b=u.section!==k&&!t?k=u.section:null;return a`${b?a`<li class="palette-head small" role="presentation">${b}</li>`:null}
          <li id=${`pal-${$}`} class="item" role="option" aria-selected=${$===s}
              onMouseMove=${()=>o($)} onClick=${()=>E(u)}>
            <${_} spec=${u.sym} /><span class="label">${u.label}</span><span class="detail small">${u.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function Ls(e){return["Groups","Runs","Commands"].indexOf(e)}function $t(e,t=[]){let n=new Map,s=(i,l={})=>({path:i,name:i==="."?"local":i.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let i of e)n.set(i.path,s(i.path,i));(t.length===0||t.some(i=>i.name==="local"))&&!n.has(".")&&n.set(".",s("."));for(let i of t){let l=i.name==="local"?".":i.name;n.has(l)||n.set(l,s(l)),Object.assign(n.get(l),{state:i.state,error:i.error})}for(let i of n.values()){if(V(i.path))continue;let l=i.path.lastIndexOf("/"),d=l<0?".":i.path.slice(0,l);(n.get(d)??n.get(ke(i.path))??n.get(".")).children.push(i)}for(let i of n.values())i.children.sort((l,d)=>l.name.localeCompare(d.name));let r=[...n.values()].filter(i=>i.path!=="."&&V(i.path)).sort((i,l)=>i.name.localeCompare(l.name)),c=n.get(".");return c?[c,...r]:r}function Is(e,t,n,s=new Set){let o=[],r=n.toLowerCase(),c=i=>{(!r||i.path.toLowerCase().includes(r)||Os(i,r))&&(o.push(i),(r||(V(i.path)?!s.has(i.path):t.has(i.path)))&&i.children.forEach(c))};return e.forEach(c),o}function Os(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Os(n,t))}function zs(e,t){if(V(t))return e;let n=t.lastIndexOf("/"),s=n<0?".":t.slice(0,n),o=r=>r.path===s?r:r.children.map(o).find(c=>c)??null;return e.map(o).find(r=>r)?.children??[]}function Bs(e){return V(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function As(){let e=N(q),t=x(ce()),[n,s]=y(()=>new Set(ge("open",[]))),[o,r]=y(()=>new Set(ge("closed-hosts",[]))),[c,i]=y(""),l=L(null),d=e.page==="group"?e.path:null,v=$t(P(t.data),t.data?.meta?.sources??[]),m=Is(v,La(n,d),c,o),p=f=>V(f)?!o.has(f):n.has(f),h=(f,k)=>{let u=k??!p(f);if(V(f)){let b=new Set(o);u?b.delete(f):b.add(f),ve("closed-hosts",[...b]),r(b);return}let $=new Set(n);u?$.add(f):$.delete(f),ve("open",[...$]),s($)},g=L(d);return T(()=>{d!==g.current&&d&&!V(d)&&o.has(ke(d))&&h(ke(d),!0),g.current=d},[d]),a`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${w} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${c} aria-label="Filter groups"
        onInput=${f=>i(f.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${f=>{let k=[...l.current?.querySelectorAll("a.tree-item")??[]],u=k.indexOf(document.activeElement),$=m[u];switch(f.key){case"ArrowDown":k[Math.min(k.length-1,u+1)]?.focus();break;case"ArrowUp":k[Math.max(0,u-1)]?.focus();break;case"ArrowRight":$?.children.length&&h($.path,!0);break;case"ArrowLeft":$?.children.length&&p($.path)?h($.path,!1):$&&k[m.findIndex(b=>b.path===Ra($.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${m.map(f=>a`<${Pa} key=${f.path} node=${f} current=${f.path===d}
        open=${p(f.path)||!!c} onToggle=${()=>h(f.path)} />`)}
    </div>
  </nav>`}function Pa(e){let t=e.node,n=()=>je(t.path),s=t.children.length>0,o=t.state==="unreachable";return a`<a class=${`tree-item${e.current?" current":""}${V(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${s?e.open:void 0}
      style=${`padding-inline-start:${8+Bs(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${r=>{r.metaKey||r.ctrlKey||(r.preventDefault(),R(S(t.path)))}}>
    <span class="twisty" onClick=${r=>{r.preventDefault(),r.stopPropagation(),e.onToggle()}}>
      ${s?a`<${w} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${V(t.path)?a`<${_} size=${14} spec=${{icon:o?"cloud-off":"server",tone:"muted",label:o?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?a`<${_} spec=${M("run","running")} size=${14} />`:null}
      ${t.failed?a`<${_} spec=${{...M("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Ra(e){if(V(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function La(e,t){if(!t||t===".")return e;let n=new Set(e),s=t.split("/");for(let o=1;o<s.length;o++)n.add(s.slice(0,o).join("/"));return n}function Ks(){let e=N(q),t=N(Q),n=N(ee),s=N(fe),o=L(null);T(()=>qt(()=>o.current),[]),T(()=>(addEventListener("keydown",Hs),()=>removeEventListener("keydown",Hs)),[]);let r=e.page==="group"&&e.drawer,c;switch(e.page){case"group":c=a`<${Es} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":c=a`<${Ms} id=${e.id} />`;break;case"settings":c=a`<${qn} />`;break;case"timeline":c=a`<${Ds} key=${e.from} from=${e.from} />`;break;default:c=a`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return me||!1?a`<main class="main render-main" ref=${o}>${c}</main>`:a`<div class=${`shell${t?"":" no-sidebar"}${r?" with-drawer":""}`}>
    <${Yn} />
    ${t?a`<${As} />`:null}
    <main class="main" ref=${o}>${c}</main>
    ${r?a`<${ls} path=${e.path} run=${e.run} />`:null}
    <${Jn} />
    ${n!==null?a`<${_s} query=${n} />`:null}
    ${s?a`<${Ia} />`:null}
    <${Ps} />
  </div>`}function Hs(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),ee.set(ee.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Q.set(!Q.value);return}if(e.key==="Escape"){if(ee.value!==null||fe.value)return;let s=q.value;return s.page==="group"&&s.run?R(S(s.path,{drawer:!0}),{replace:!0}):s.page==="group"&&s.drawer?R(S(s.path),{replace:!0}):void 0}if(t||e.altKey||Vn(e)||ee.value!==null||fe.value)return;let n=q.value;switch(e.key){case"/":e.preventDefault(),ee.set("");break;case"?":fe.set(!fe.value);break;case"p":ne.set(!ne.value);break;case"i":n.page==="group"&&R(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Q.set(!Q.value);break;case"[":case"]":n.page==="group"&&_a(n.path,e.key==="]"?1:-1);break}}async function _a(e,t){let n=await Se(ce()),s=zs($t(P(n),n?.meta?.sources??[]),e),o=s.findIndex(c=>c.path===e),r=s[o+t];r&&R(S(r.path))}function Ia(){let e=L(null);return T(()=>{let t=e.current;t.showModal();let n=()=>fe.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),a`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${lt.map(([t,n])=>a`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${oe} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Yt();if(me){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(pe.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Le.n,Jt&&an()}Nn();var Oa=K("meta").then(e=>(me&&(e={...e,settings:{...e.settings,theme_mode:pe.value}}),ct(e),e));!me&&!!1&&Wt(async()=>{let[e,t]=await Promise.all([Oa,K("meta")]);e.bundle!==t.bundle?location.reload():ct(t)});Ht(a`<${Ks} />`,document.getElementById("app"));
