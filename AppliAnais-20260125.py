# ... (après l'appel au coach)
            txt = res.text
            
            # Vérification plus souple : cherche le mot BRAVO n'importe où au début
            nettoyage_txt = txt.strip().upper()
            if nettoyage_txt.startswith("BRAVO") or "BRAVO" in nettoyage_txt[:10]:
                st.session_state.xp += 20
                if activer_ballons:
                    st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            st.session_state.attente_reponse = True
            st.rerun()
