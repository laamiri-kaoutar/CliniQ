import pytest
from unittest.mock import MagicMock
from app.services.query_service import query_service

def test_medical_query_processing():
    # 1. SETUP : Simulation de la DB et de l'User
    mock_db = MagicMock()
    mock_user = MagicMock(id=1, username="Dr_Kaoutar")
    
    # Simulation du résultat brut de ton pipeline
    mock_pipeline_result = {
        "answer": [{"text": "Le protocole recommandé est l'usage de X."}],
        "sources": ["guide_clinique_2026.pdf"]
    }
    # On mocke uniquement la méthode search du pipeline
    query_service.pipeline.search = MagicMock(return_value=mock_pipeline_result)

    # 2. EXECUTION
    result = query_service.create_medical_query(mock_db, mock_user, "Quel est le protocole ?")

    # 3. ASSERTS : Preuves de bon fonctionnement
    # Vérifie que le texte est extrait correctement de la liste
    assert result["response_text"] == "Le protocole recommandé est l'usage de X."
    # Vérifie que la DB enregistre bien l'action
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()