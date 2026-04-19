from train_botsim import DEFAULT_BOTSIM_MODEL_PATH, train_botsim


if __name__ == "__main__":
    print("[main] Compatibility entry point. Use train_botsim.py as the maintained BotSim trainer.")
    summary = train_botsim(model_output_path=DEFAULT_BOTSIM_MODEL_PATH)
    print(f"[main] model: {summary['paths']['model']}")
