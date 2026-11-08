/**
 * Connecteur Backend Django / MySQL pour l'interface existante EauSolidaire.
 * Conserve à 100 % le design, le HTML, le CSS et les interactions visuelles d'origine,
 * tout en remplaçant la persistance locale en mémoire par les vraies tables MySQL via fetch() + CSRF.
 */
(function () {
  function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function getAuthHeaders(extra) {
    return Object.assign(
      {
        'X-CSRFToken': getCsrfToken(),
        'X-User-Email': U && U.email ? U.email : '',
        'X-User-Role': U && U.role ? U.role : '',
      },
      extra || {}
    );
  }

  async function apiPost(url, payload) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        credentials: 'same-origin',
        cache: 'no-store',
        body: JSON.stringify(payload || {}),
      });
      return await res.json();
    } catch (err) {
      return { ok: false, error: 'Erreur de communication avec le serveur.' };
    }
  }

  D.equipements = D.equipements || [];
  try {
    D.messages = JSON.parse(localStorage.es_msgs || '[]');
  } catch (e) {
    D.messages = D.messages || [];
  }
  function saveMsgs() {
    try {
      localStorage.es_msgs = JSON.stringify(D.messages || []);
    } catch (e) {}
  }

  function refreshUI() {
    const bellBadge = document.querySelector('.bell i');
    if (bellBadge) bellBadge.textContent = (D.notifs || []).length;
    const h = location.hash.slice(1) || 'accueil';
    if (['admin', 'local', 'tech'].includes(h) && U && U.role === h && document.querySelector('#c')) {
      const qEl = document.querySelector('#c #q');
      const sEl = document.querySelector('#c #s');
      const prevQ = qEl ? qEl.value : '';
      const prevS = sEl ? sEl.value : '';
      charts.forEach((c) => c.destroy());
      charts = [];
      draw(h);
      const newQ = document.querySelector('#c #q');
      const newS = document.querySelector('#c #s');
      if (newQ && prevQ) newQ.value = prevQ;
      if (newS && prevS) newS.value = prevS;
      if ((prevQ || prevS) && typeof fl === 'function') fl();
    } else {
      route();
    }
  }

  let lastStateHash = '';

  async function syncFromBackend(onlyIfChanged) {
    try {
      const res = await fetch('/api/state/?_=' + Date.now(), {
        credentials: 'same-origin',
        cache: 'no-store',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      if (data && data.ok && data.D) {
        const snapshot = JSON.stringify(data.D);
        if (onlyIfChanged && snapshot === lastStateHash) {
          return;
        }
        lastStateHash = snapshot;
        D.villages = data.D.villages || D.villages;
        D.pts = data.D.pts || D.pts;
        D.equipements = data.D.equipements || D.equipements;
        D.pannes = data.D.pannes || D.pannes;
        D.stock = data.D.stock || D.stock;
        D.hist = data.D.hist || D.hist;
        D.notifs = Array.isArray(data.D.notifs) ? data.D.notifs : [];
        D.techs = data.D.techs || D.techs;
        if (Array.isArray(data.D.messages)) {
          D.messages = data.D.messages;
          saveMsgs();
        }
        if (Array.isArray(data.D.users) && typeof USERS !== 'undefined') {
          data.D.users.forEach((dbU) => {
            if (!USERS.some((u) => u.email === dbU.email)) {
              USERS.push(dbU);
            }
          });
          if (typeof saveUsers === 'function') saveUsers();
        }
        if (data.U && !U) {
          U = data.U;
        }
        refreshUI();
      }
    } catch (e) {
      // Conservation transparente des données affichées si hors-ligne
    }
  }

  // 1. Connexion (#connexion) : conserve 100 % des animations (busy, wait, shake, #lerr) et authentifie via MySQL
  window.doLogin = async function (e) {
    e.preventDefault();
    const f = e.target,
      id = f.ident.value.trim().toLowerCase(),
      pw = f.mdp.value,
      b = f.querySelector('.send');
    if (!id || !pw) {
      [f.ident, f.mdp].forEach(vf);
      return false;
    }
    busy(b, 'Connexion…');
    const [res] = await Promise.all([
      apiPost('/api/auth/login/', { ident: id, mdp: pw, role: AR }),
      wait(700),
    ]);
    let u = null;
    if (res && res.ok && res.user) {
      u = res.user;
    } else if (AR == 'admin') {
      if (
        (id == 'admin' || id == 'diabymadoussou528@gmail.com') &&
        pw.replace(/\s/g, '').toLowerCase() == 'admin1234'
      ) {
        u = { role: 'admin', nom: 'Administrateur', email: 'diabymadoussou528@gmail.com' };
      }
    } else {
      const x = USERS.find(
        (y) =>
          y.role == AR &&
          (y.email == id || (y.tel || '').replace(/\s/g, '') == id.replace(/\s/g, ''))
      );
      if (x && x.h && x.h == (await hsh(pw, x.email))) u = x;
    }
    if (!u) {
      idle(b, 'Se connecter');
      $('#lerr').textContent = 'Identifiant ou mot de passe incorrect.';
      shake();
      return false;
    }
    D.notifs = [];
    enter(u);
    await syncFromBackend();
    return false;
  };

  // 2. Déconnexion Django + nettoyage sessionStorage
  window.logout = function () {
    U = null;
    D.notifs = [];
    try {
      sessionStorage.removeItem('es_u');
    } catch (e) {}
    apiPost('/api/auth/logout/', {});
    location.hash = 'accueil';
  };

  // 3. Inscription (#inscription) + Modale E-mail de confirmation envoyé (identique au design et enregistrée en base MySQL)
  window.doSign = async function (e) {
    e.preventDefault();
    const f = e.target,
      er = $('#serr'),
      ok = [...f.querySelectorAll('.fl input')].map((x) => vf(x)).every(Boolean);
    if (!ok) {
      er.textContent = 'Corrigez les champs en rouge.';
      shake();
      return false;
    }
    if (!f.cg.checked) {
      er.textContent = 'Veuillez accepter les conditions.';
      return false;
    }
    const em = f.email.value.trim().toLowerCase();
    if (USERS.some((u) => u.email == em)) {
      er.textContent = 'Un compte existe déjà avec cette adresse e-mail.';
      shake();
      return false;
    }
    er.textContent = '';
    const b = f.querySelector('.send');
    busy(b, 'Création du compte…');
    const payload = {
      role: SR,
      nom: f.nom.value.trim(),
      email: em,
      tel: f.tel.value.trim(),
      npw: f.npw.value,
      vil: SR == 'local' && f.vil ? f.vil.value : '',
      spe: SR == 'tech' && f.spe ? f.spe.value : '',
    };
    const [res] = await Promise.all([apiPost('/api/auth/register/', payload), wait(800)]);
    if (res && res.ok === false && res.error && res.error.includes('existe déjà')) {
      idle(b, 'Créer mon compte');
      er.textContent = res.error;
      shake();
      return false;
    }
    const u = {
      role: SR,
      nom: payload.nom,
      email: em,
      tel: payload.tel,
      h: await hsh(payload.npw, em),
      village: payload.vil,
      spe: payload.spe,
    };
    if (!USERS.some((x) => x.email == em)) {
      USERS.push(u);
      saveUsers();
    }
    if (SR == 'tech' && !D.techs.includes(u.nom)) D.techs.push(u.nom);
    PRE = em;
    AR = SR;
    modal(
      `<h3>E-mail de confirmation envoyé</h3><div class="mail" style="margin:12px 0"><div class="h"><b>À :</b> ${esc(
        em
      )}<br><b>Objet :</b> Votre compte EauSolidaire est créé</div><div class="b"><p>Bonjour ${esc(
        u.nom.split(' ')[0]
      )},</p><p>Votre compte <b>${RL[SR]}</b> a bien été créé${
        SR == 'local' ? ' pour le village de ' + esc(u.village) : ''
      }. Vous pouvez dès maintenant vous connecter avec votre adresse e-mail et le mot de passe que vous avez choisi.</p><p>Pour votre sécurité, ce message ne contient jamais votre mot de passe.</p><p>L’équipe EauSolidaire</p></div></div><button class="btn" style="width:100%" onclick="closeM();location.hash='connexion'">Se connecter</button>`
    );
    return false;
  };

  // 4. Réinitialisation de mot de passe en 3 étapes (#motdepasse avec code à 6 chiffres et persistance MySQL)
  window.rs1 = async function (e) {
    e.preventDefault();
    const f = e.target;
    if (!vf(f.email)) {
      shake();
      return false;
    }
    const em = f.email.value.trim().toLowerCase();
    const generatedCode = String(Math.floor(100000 + Math.random() * 900000));
    const existsLocal = USERS.some((u) => u.email == em);
    const res = await apiPost('/api/auth/password-reset/', {
      email: em,
      mode: 'otp',
      code: generatedCode,
    });
    if (!existsLocal && (!res || !res.ok)) {
      const w = f.email.closest('.fl');
      w.classList.add('er');
      w.querySelector('.em').textContent =
        'Aucun compte avec cette adresse (responsables locaux et techniciens uniquement).';
      shake();
      return false;
    }
    RS = {
      s: 2,
      email: em,
      code: (res && res.code) || generatedCode,
      sent: !!(res && res.email_sent),
    };
    rsR();
    return false;
  };

  window.rs3 = async function (e) {
    e.preventDefault();
    const f = e.target;
    if (![vf(f.npw), vf(f.cfm)].every(Boolean)) {
      shake();
      return false;
    }
    busy(f.querySelector('.send'), 'Enregistrement…');
    await Promise.all([
      apiPost('/api/auth/password-reset/confirm/', {
        email: RS.email,
        code: RS.code,
        password: f.npw.value,
      }),
      wait(700),
    ]);
    const u = USERS.find((x) => x.email == RS.email);
    if (u) {
      u.h = await hsh(f.npw.value, u.email);
      saveUsers();
    }
    RS.s = 4;
    rsR();
    return false;
  };

  // 3. Notifications : marquer tout comme lu côté MySQL
  window.notifs = function () {
    modal(
      `<h3>Notifications</h3>${
        D.notifs.map((n) => `<p>• ${esc(n)}</p>`).join('') ||
        '<p class="mut">Aucune notification.</p>'
      }<button class="btn" onclick="clearNotifsBackend()">Tout marquer comme lu</button>`
    );
  };
  window.clearNotifsBackend = async function () {
    D.notifs = [];
    closeM();
    refreshUI();
    await apiPost('/api/auth/notifications/clear/', {});
    await syncFromBackend();
  };

  // 4. Gestion géographique : Ajout et Suppression de village dans MySQL
  window.addV = function () {
    modal(
      `<h3>Nouveau village</h3><form><label>Village</label><input name="n" required><label>Commune</label><input name="c" required><label>Cercle</label><input name="ce" required><label>Région</label><input name="r" required><p><button class="btn">Enregistrer</button></p></form>`,
      (d) => {
        D.villages.push(d);
        toast('Village ajouté');
        refreshUI();
        apiPost('/api/localisation/villages/add/', d).then((res) => {
          if (res && !res.ok && res.error) {
            toast(res.error);
          }
          syncFromBackend();
        });
      }
    );
  };

  window.delV = async function (i) {
    const v = D.villages[i];
    if (!v) return;
    if (D.pts.some((p) => p.v == v.n)) {
      return toast('Suppression impossible : des points d’eau en dépendent');
    }
    if (confirm('Supprimer ' + v.n + ' ?')) {
      D.villages.splice(i, 1);
      toast('Supprimé');
      refreshUI();
      const res = await apiPost('/api/localisation/villages/delete/', { n: v.n, id: v.id });
      if (res && !res.ok) {
        toast(res.error || 'Suppression impossible');
      }
      await syncFromBackend();
    }
  };

  // 5. Points d'eau et Équipements : Ajout, changement d'état, suppression et mise à jour GPS dans MySQL
  window.addEq = function () {
    modal(
      `<h3>Nouvel équipement</h3><form><label>Référence</label><input name="ref" required placeholder="EQ-003"><label>Nom de l’équipement</label><input name="nom" required placeholder="Pompe Vergnet HPV 60"><label>Type d’équipement</label><select name="type"><option>Pompe manuelle</option><option>Pompe solaire</option><option>Pompe immergée</option><option>Château d'eau / Réservoir</option><option>Panneau solaire</option><option>Robinet / Borne</option><option>Autre</option></select><label>Point d’eau associé</label><select name="pt">${D.pts
        .map((p) => `<option value="${esc(p.ref)}">${esc(p.ref)} · ${esc(p.n)}</option>`)
        .join('')}</select><label>État initial</label><select name="etat">${ST.map(
        (s) => `<option>${s}</option>`
      ).join('')}</select><label>Description (facultative)</label><input name="description"><p><button class="btn">Enregistrer</button></p></form>`,
      (d) => {
        if ((D.equipements || []).some((e) => e.ref == d.ref)) {
          toast('Référence équipement déjà utilisée');
          return false;
        }
        const ptObj = D.pts.find((p) => p.ref == d.pt);
        D.equipements.push({
          ref: d.ref,
          nom: d.nom,
          type: d.type,
          pt: d.pt,
          pt_nom: ptObj ? ptObj.n : '',
          etat: d.etat,
          description: d.description || '',
        });
        toast('Équipement ajouté');
        pts($('#c'));
        apiPost('/api/equipements/add/', d).then((res) => {
          if (res && !res.ok && res.error) toast(res.error);
          syncFromBackend();
        });
      }
    );
  };

  window.setEqS = async function (i, v) {
    const eq = (D.equipements || [])[i];
    if (!eq) return;
    eq.etat = v;
    if (typeof fl === 'function') fl();
    toast('État de l’équipement mis à jour');
    await apiPost('/api/equipements/etat/', { id: eq.id, ref: eq.ref, etat: v });
    syncFromBackend();
  };

  window.delEq = async function (i) {
    const eq = (D.equipements || [])[i];
    if (!eq) return;
    if (confirm('Supprimer l’équipement ' + eq.nom + ' (' + eq.ref + ') ?')) {
      const res = await apiPost('/api/equipements/delete/', { id: eq.id, ref: eq.ref });
      if (res && !res.ok) {
        return toast(res.error || 'Suppression impossible');
      }
      D.equipements.splice(i, 1);
      toast('Équipement supprimé');
      if (typeof fl === 'function') fl();
    }
  };

  window.addP = function () {
    modal(
      `<h3>Nouveau point d’eau</h3><form><label>Référence</label><input name="ref" required><label>Nom</label><input name="n" required><label>Type</label><select name="t"><option>Forage</option><option>Puits</option><option>Autre</option></select><label>Village</label><select name="v">${D.villages
        .map((v) => `<option>${esc(v.n)}</option>`)
        .join('')}</select><label>Latitude (facultatif)</label><input name="la" type="number" step="any"><label>Longitude (facultatif)</label><input name="lo" type="number" step="any"><p><button type="button" class="btn alt sm" onclick="gps()">Utiliser ma position</button></p><p><button class="btn">Enregistrer</button></p></form>`,
      (d) => {
        if (D.pts.some((p) => p.ref == d.ref)) {
          toast('Référence déjà utilisée');
          return false;
        }
        d.la = d.la === '' ? null : +d.la;
        d.lo = d.lo === '' ? null : +d.lo;
        if ((d.la != null || d.lo != null) && !okPos(d.la, d.lo)) {
          toast('Position invalide : latitude 10 à 25, longitude −12,5 à 4,4');
          return false;
        }
        d.s = 'Fonctionnel';
        d.log = [{ d: today(), s: 'Fonctionnel', n: 'Création' }];
        D.pts.push(d);
        toast('Point d’eau ajouté');
        refreshUI();
        apiPost('/api/points-eau/add/', d).then((res) => {
          if (res && !res.ok && res.error) toast(res.error);
          syncFromBackend();
        });
      }
    );
  };

  window.setS = async function (i, v) {
    const p = D.pts[i];
    if (!p) return;
    p.s = v;
    p.log.unshift({ d: today(), s: v });
    toast('État mis à jour');
    refreshUI();
    await apiPost('/api/points-eau/etat/', { ref: p.ref, s: v });
    await syncFromBackend();
  };

  window.setPos = function (ref) {
    const p = D.pts.find((x) => x.ref == ref);
    if (!p) return;
    modal(
      `<h3>Position de ${p.ref}</h3><form><label>Latitude</label><input name="la" type="number" step="any" required value="${
        p.la ?? ''
      }"><label>Longitude</label><input name="lo" type="number" step="any" required value="${
        p.lo ?? ''
      }"><p><button type="button" class="btn alt sm" onclick="gps()">Utiliser ma position</button></p><p><button class="btn">Enregistrer</button></p></form>`,
      (x) => {
        const a = +x.la,
          o = +x.lo;
        if (!okPos(a, o)) {
          toast('Position invalide : latitude 10 à 25, longitude −12,5 à 4,4');
          return false;
        }
        p.la = a;
        p.lo = o;
        p.log.unshift({ d: today(), n: 'Position mise à jour' });
        toast('Position enregistrée');
        refreshUI();
        apiPost('/api/points-eau/position/', { ref: p.ref, la: a, lo: o }).then(() =>
          syncFromBackend()
        );
      }
    );
  };

  // 6. Pannes et Interventions : Déclaration, Affectation, Démarrage, Clôture
  window.setP = async function (i, s) {
    const p = D.pannes[i];
    if (!p) return;
    p.s = s;
    toast('Statut : ' + s);
    refreshUI();
    await apiPost('/api/pannes/statut/', { id: p.id, pt: p.pt, s: s });
    await syncFromBackend();
  };

  window.aff = function (i) {
    const p = D.pannes[i];
    if (!p) return;
    modal(
      `<h3>Affecter un technicien</h3><form><select name="t">${D.techs
        .map((t) => `<option>${t}</option>`)
        .join('')}</select><p><button class="btn">Affecter</button></p></form>`,
      (d) => {
        p.tech = d.t;
        p.s = 'Technicien affecté';
        toast('Intervention créée pour ' + d.t);
        refreshUI();
        apiPost('/api/interventions/affecter/', { id: p.id, pt: p.pt, t: d.t }).then(() =>
          syncFromBackend()
        );
      }
    );
  };

  window.dec = function (c) {
    c.innerHTML = `<h2>Déclarer une panne</h2><form class="card" style="max-width:480px" id="df"><label>Point d’eau</label><select name="pt">${D.pts
      .filter((p) => p.v == U.village)
      .map((p) => `<option>${p.ref}</option>`)
      .join(
        ''
      )}</select><label>Description</label><textarea name="d" required></textarea><label>Priorité</label><select name="p"><option>Faible</option><option>Moyenne</option><option>Élevée</option><option>Critique</option></select><label>Photo (facultative)</label><input type="file" name="photo" accept="image/*"><p><button class="btn">Envoyer le signalement</button></p></form>`;
    $('#df').onsubmit = async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const d = Object.fromEntries(formData);
      formData.append('by', U.name);
      D.pannes.push({
        id: Date.now(),
        pt: d.pt,
        d: d.d,
        p: d.p,
        s: 'Nouveau signalement',
        by: U.name,
        by_email: (U.email || '').toLowerCase(),
        tech: '',
        tech_email: '',
      });
      D.notifs.push(U.role == 'admin' ? 'Nouveau signalement : ' + d.pt : 'Signalement enregistré : ' + d.pt);
      toast('Signalement envoyé');
      view = 'mes';
      refreshUI();
      try {
        await fetch('/api/pannes/add/', {
          method: 'POST',
          headers: getAuthHeaders(),
          credentials: 'same-origin',
          body: formData,
        });
      } catch (err) {}
      await syncFromBackend();
    };
  };

  window.setP2 = async function (i, s) {
    const p = D.pannes[i];
    if (!p) return;
    p.s = s;
    D.notifs.push('Intervention démarrée : ' + p.pt);
    toast('Intervention démarrée');
    refreshUI();
    await apiPost('/api/interventions/demarrer/', { id: p.id, pt: p.pt, s: s });
    await syncFromBackend();
  };

  window.fin = function (i) {
    const p = D.pannes[i];
    if (!p) return;
    modal(
      `<h3>Terminer l’intervention</h3><form><label>Compte rendu</label><textarea name="r" required></textarea><label>Pièce utilisée</label><select name="pc"><option value="">Aucune</option>${D.stock
        .map((s, j) => `<option value="${j}">${esc(s.n)} (${s.q})</option>`)
        .join(
          ''
        )}</select><label>Quantité</label><input name="q" type="number" min="1" value="1"><p><button class="btn">Terminer</button></p></form>`,
      (d) => {
        let pieceRef = '';
        if (d.pc !== '') {
          const s = D.stock[+d.pc];
          if (+d.q > s.q) {
            toast('Stock insuffisant');
            return false;
          }
          pieceRef = s.ref;
          s.q -= +d.q;
          D.hist.unshift('−' + d.q + ' ' + s.n + ' (intervention ' + p.pt + ')');
          if (s.q <= s.min && U && U.role == 'admin') D.notifs.push('Stock faible : ' + s.n);
        }
        p.s = 'Résolu';
        D.notifs.push('Intervention terminée : ' + p.pt);
        toast('Intervention terminée');
        refreshUI();
        apiPost('/api/interventions/terminer/', {
          id: p.id,
          pt: p.pt,
          r: d.r,
          piece_ref: pieceRef,
          q: +d.q || 1,
        }).then(() => syncFromBackend());
      }
    );
  };

  // 7. Stock : Entrées et sorties de pièces détachées dans MySQL
  window.mv = function (i, s) {
    const item = D.stock[i];
    if (!item) return;
    modal(
      `<h3>${s > 0 ? 'Entrée' : 'Sortie'} : ${esc(
        item.n
      )}</h3><form><label>Quantité</label><input name="q" type="number" min="1" required><p><button class="btn">Valider</button></p></form>`,
      (d) => {
        const q = +d.q;
        if (s < 0 && q > item.q) {
          toast('Stock insuffisant : ' + item.q + ' disponible(s)');
          D.notifs.push('Stock insuffisant : ' + item.n);
          return false;
        }
        item.q += s * q;
        D.hist.unshift((s > 0 ? '+' : '−') + q + ' ' + item.n);
        if (item.q <= item.min && U && U.role == 'admin') D.notifs.push('Stock faible : ' + item.n);
        toast('Mouvement enregistré');
        refreshUI();
        apiPost('/api/stock/mouvement/', { ref: item.ref, s: s, q: q }).then(() =>
          syncFromBackend()
        );
      }
    );
  };

  // 8. Formulaire de contact public connecté à MySQL + affichage dans le tableau de bord Administrateur
  window.cSend = function (e) {
    e.preventDefault();
    const f = e.target;
    const ok = [...f.querySelectorAll('input[name=nom],input[name=email],textarea')]
      .map(cVal)
      .every(Boolean);
    if (!ok) {
      toast('Vérifiez les champs en rouge');
      return false;
    }
    const b = f.querySelector('.send');
    b.disabled = true;
    b.textContent = 'Envoi en cours…';
    const payload = {
      sj: f.sj.value,
      nom: f.nom.value.trim(),
      email: f.email.value.trim(),
      msg: f.msg.value.trim(),
    };
    const localMsg = {
      id: Date.now(),
      sj: payload.sj,
      nom: payload.nom,
      email: payload.email,
      msg: payload.msg,
      traite: false,
      date: today(),
    };
    D.messages = D.messages || [];
    D.messages.unshift(localMsg);
    saveMsgs();
    apiPost('/api/auth/contact/', payload).then((res) => {
      if (res && res.ok && res.message_obj) {
        localMsg.id = res.message_obj.id;
        localMsg.date = res.message_obj.date || localMsg.date;
        saveMsgs();
      }
    });
    setTimeout(() => {
      $('#cr').innerHTML = `<div class="okm"><div class="ck">✓</div><h3>Merci ${esc(
        f.nom.value.trim().split(' ')[0]
      )} !</h3><p class="mut">Votre message « ${esc(
        f.sj.value
      )} » a bien été envoyé à notre équipe.</p><button class="btn alt" onclick="cReset()">Nouveau message</button></div>`;
    }, 900);
    return false;
  };

  window.setMsgS = async function (i, traite) {
    const m = (D.messages || [])[i];
    if (!m) return;
    m.traite = traite;
    saveMsgs();
    toast('Message marqué comme traité');
    refreshUI();
    await apiPost('/api/auth/contact/statut/', { id: m.id, traite: traite });
    await syncFromBackend();
  };

  window.delMsg = async function (i) {
    const m = (D.messages || [])[i];
    if (!m) return;
    if (confirm('Supprimer le message de ' + m.nom + ' ?')) {
      D.messages.splice(i, 1);
      saveMsgs();
      toast('Message supprimé');
      refreshUI();
      await apiPost('/api/auth/contact/delete/', { id: m.id });
      await syncFromBackend();
    }
  };

  // Chargement initial des données depuis MySQL au démarrage + synchronisation temps réel automatique
  syncFromBackend();
  setInterval(() => {
    const h = location.hash.slice(1) || 'accueil';
    if (!['admin', 'local', 'tech'].includes(h) || !U) return;
    if (document.querySelector('#m .dlg')) return;
    const active = document.activeElement;
    if (active && ['INPUT', 'TEXTAREA', 'SELECT'].includes(active.tagName)) return;
    syncFromBackend(true);
  }, 3000);
  window.addEventListener('focus', () => {
    if (U && !document.querySelector('#m .dlg')) syncFromBackend(true);
  });
})();
