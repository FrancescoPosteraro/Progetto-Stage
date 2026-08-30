import sys
import subprocess


if len(sys.argv) < 2:
    print("Uso: python run.py [scraper|api|test]")
    sys.exit(1)


command = sys.argv[1]


if command == "test":

    subprocess.run(["pytest"], check=True)


elif command == "scraper":

    subprocess.run(
        [sys.executable, "-m", "web_scraper.web_scraper"],
        check=True
    )


elif command == "api":

    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--reload"
        ],
        check=True
    )


else:

    print(f"Comando non riconosciuto: {command}")
    print("Comandi disponibili: scraper, api, test")
    sys.exit(1)