import streamlit as st
import requests

st.set_page_config(page_title="CliniQ - Assistant RAG", page_icon="🔍")

if not st.session_state.get("authenticated"):
    st.warning("Veuillez vous connecter sur la page d'accueil.")
    st.stop()

st.title("Support Décisionnel RAG")
st.markdown("---")

query_text = st.text_area("Question clinique :", placeholder="Ex: Quelle est la procédure pour une transplantation hépatique ?")

if st.button("Analyser et Générer la réponse"):
    if query_text:
        with st.spinner("Génération en cours..."):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                payload = {"query_text": query_text}
                
                response = requests.post(
                    "http://backend:8000/chat/query", 
                    json=payload, 
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # --- SÉCURITÉ : Recherche de la réponse dans le JSON ---
                    # Ton backend peut renvoyer 'answer' OU 'response_text'
                    assistant_answer = data.get("answer") or data.get("response_text")
                    
                    if assistant_answer:
                        st.subheader("Réponse de l'Assistant")
                        st.success(assistant_answer)
                    else:
                        st.error("Le backend n'a pas renvoyé de champ 'answer' ou 'response_text'.")
                        st.json(data) # Affiche le JSON brut pour débugger devant le formateur
                    
                    with st.expander("Détails de confiance & Sources"):
                        # Vérification des champs de métriques
                        f_score = data.get('faithfulness_score') or data.get('faithfulness')
                        st.write(f"**Score de fidélité :** {f_score if f_score is not None else 'N/A'}")
                        
                        st.write("**Documents sources :**")
                        sources = data.get("source_documents") or data.get("sources", [])
                        if sources:
                            for doc in sources:
                                st.write(f"- {doc}")
                        else:
                            st.write("Aucune source listée.")
                
                elif response.status_code == 401:
                    st.error("Session expirée. Veuillez vous reconnecter.")
                else:
                    st.error(f"Erreur Backend {response.status_code}: {response.text}")
                    
            except Exception as e:
                # Utilisation de repr(e) pour voir l'erreur réelle sans crash de clé
                st.error(f"Erreur de communication : {repr(e)}")
    else:
        st.warning("Veuillez saisir une question.")