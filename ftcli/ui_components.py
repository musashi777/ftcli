from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import questionary
from questionary import Style

console = Console()

custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
])

def create_main_menu() -> str:
    """Crée et affiche un menu principal interactif."""
    
    ascii_logo = """
   ╔═╗╔╦╗╔═╗┬ ┬ 
   ╠╣  ║ ║  │ │ 
   ╚   ╩ ╚═╝┴─┘┴ 
    """
    
    console.print(Panel(Align.center(Text(ascii_logo, style="bold cyan")),
                        title="[bold]FTCli - Assistant Recherche d'Emploi[/bold]",
                        border_style="cyan"))

    choices = [
        "🔍 Rechercher des offres d'emploi",
        "🏢 Trouver des entreprises à potentiel",
        "📊 Voir le tableau de bord",
        "📋 Gérer le suivi des candidatures",
        "👤 Gérer mes profils CV",
        "🤖 Lancer l'agent IA",
        "❌ Quitter"
    ]
    
    choice = questionary.select(
        "Que souhaitez-vous faire ?",
        choices=choices,
        style=custom_style,
        qmark="➜",
        pointer="▶",
    ).ask()
    
    return choice if choice else "Quitter"
