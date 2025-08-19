import click

from .main import analyze


def main():
    analyze(standalone_mode=False)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        # click may raise SystemExit after handling --help etc.
        if e.code not in (0, None):
            raise

