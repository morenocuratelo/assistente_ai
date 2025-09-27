import os
import sys
import json
import asyncio
import argparse
import pandas as pd
from llama_index.core import (
    StorageContext,
    load_index_from_storage,
    VectorStoreIndex,
    SimpleDirectoryReader
)
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.evaluation import (
    FaithfulnessEvaluator,
    RelevancyEvaluator,
    ContextRelevancyEvaluator,
)
from llama_index.llms.ollama import Ollama
from llama_index.core.query_engine import RetrieverQueryEngine
from config import initialize_services

DB_STORAGE_DIR = "db_memoria"

async def main():
    parser = argparse.ArgumentParser(description="Esegue la valutazione automatica del sistema RAG.")
    parser.add_argument("--focus_file", help="Esegue la valutazione solo su un file specifico.")
    args = parser.parse_args()

    print("--- Avvio del Sistema di Valutazione Automatica ---")
    initialize_services()

    try:
        storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
        index = load_index_from_storage(storage_context)
        print("Indice caricato correttamente dalla memoria.")
    except FileNotFoundError:
        print(f"ERRORE: La cartella della memoria '{DB_STORAGE_DIR}' non è stata trovata.")
        sys.exit(1)

    try:
        with open("evaluation_dataset.json", "r", encoding="utf-8") as f:
            eval_data = json.load(f)

        # --- MODIFICA CHIAVE: Controllo robusto del formato del dataset ---
        if isinstance(eval_data, list):
            print("\n--- ERRORE: FORMATO DATASET OBSOLETO ---")
            print("Il file 'evaluation_dataset.json' è in un formato vecchio (una lista).")
            print("È necessario rigenerarlo per includere il nome del documento di origine.")
            print("\nSOLUZIONE: Esegui di nuovo 'generate_testset.py' per il tuo file di destinazione.")
            sys.exit(1)
            
        eval_source_doc = eval_data.get("source_document")
        eval_questions = eval_data.get("questions", [])
        
        if not eval_source_doc or not eval_questions:
             raise ValueError("Formato JSON non valido o chiavi 'source_document'/'questions' mancanti.")

        print(f"Dataset di valutazione caricato per '{eval_source_doc}' con {len(eval_questions)} domande.")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"ERRORE: File 'evaluation_dataset.json' non trovato, corrotto o in formato non valido. ({e})")
        sys.exit(1)

    # Controllo di coerenza tra focus e dataset
    if args.focus_file and eval_source_doc != args.focus_file:
        print("\n--- ERRORE DI COERENZA ---")
        print(f"Stai cercando di eseguire un test in focus su '{args.focus_file}',")
        print(f"ma il file 'evaluation_dataset.json' contiene domande per '{eval_source_doc}'.")
        print("\nSOLUZIONE: Genera un nuovo set di test per il file corretto con:")
        print(f'python generate_testset.py "percorso/a/{args.focus_file}"')
        sys.exit(1)

    eval_llm = Ollama(model="llama3", request_timeout=120.0)
    
    faithfulness_evaluator = FaithfulnessEvaluator(llm=eval_llm)
    relevancy_evaluator = RelevancyEvaluator(llm=eval_llm)
    context_relevancy_evaluator = ContextRelevancyEvaluator(llm=eval_llm)

    if args.focus_file:
        print(f"--- ATTIVATA MODALITÀ FOCUS SUL FILE: {args.focus_file} ---")
        retriever = index.as_retriever(
            similarity_top_k=5,
            filters=MetadataFilters(filters=[ExactMatchFilter(key="file_name", value=args.focus_file)])
        )
    else:
        retriever = index.as_retriever(similarity_top_k=5)

    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        llm=eval_llm
    )

    print("Evaluators configurati. Inizio del ciclo di valutazione...\n")
    
    results = []
    for i, qa_pair in enumerate(eval_questions):
        query = qa_pair["query"]
        reference_answer = qa_pair.get("reference_answer", "N/A")
        
        print(f"--- Valutando Domanda {i+1}/{len(eval_questions)} ---")
        print(f"Query: {query}")
        
        response_obj = query_engine.query(query)
        
        faithfulness_result = await faithfulness_evaluator.aevaluate_response(response=response_obj)
        relevancy_result = await relevancy_evaluator.aevaluate_response(query=query, response=response_obj)
        context_relevancy_result = await context_relevancy_evaluator.aevaluate_response(query=query, response=response_obj)

        results.append({
            "Query": query,
            "Generated Answer": str(response_obj),
            "Reference Answer": reference_answer,
            "Faithfulness Score": faithfulness_result.score,
            "Answer Relevancy Score": relevancy_result.score,
            "Context Relevancy Score": context_relevancy_result.score
        })

    df = pd.DataFrame(results)
    
    print("\n\n--- Valutazione Completata. Generazione del Report. ---\n")
    summary = {
        "Faithfulness": f"{df['Faithfulness Score'].mean():.2f} / 1.0",
        "Answer Relevancy": f"{df['Answer Relevancy Score'].mean():.2f} / 1.0",
        "Context Relevancy": f"{df['Context Relevancy Score'].mean():.2f} / 1.0",
    }
    
    print("--- 📊 Riepilogo Punteggi Medi ---")
    for metric, score in summary.items():
        print(f"{metric}: {score}")
    print("----------------------------------\n")
    
    print(df[["Query", "Faithfulness Score", "Answer Relevancy Score", "Context Relevancy Score"]])
    df.to_csv("evaluation_results.csv", index=False)
    print("\nReport dettagliato salvato in: 'evaluation_results.csv'")


if __name__ == "__main__":
    asyncio.run(main())

