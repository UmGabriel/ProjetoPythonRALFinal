from PIL import Image, ImageDraw, ImageFont
import os, json
import pandas as pd
class ImageComposer:
    """
    Classe para compor uma imagem de fundo com múltiplos componentes (shapes) e adicionar numeração com setas.
    """
    def __init__(self, background_path, font_path=None, font_size=60):
        """
        Inicializa a classe com o caminho da imagem de fundo e a fonte para numeração.
        """
        self._check_file_exists(background_path)
        self.background = Image.open(background_path).convert('RGBA')
        self.draw = ImageDraw.Draw(self.background)
        self.components_to_draw = []
        self.font = self._load_font(font_path, font_size)

    def _check_file_exists(self, path):
        # Verifica se um arquivo existe, levantando uma exceção se não.
        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo '{path}' não encontrado!")

    def _load_font(self, path, size):
        # Tenta carregar a fonte especificada, caso contrário, usa a padrão.
        if path:
            try:
                return ImageFont.truetype(path, size)
            except (IOError, OSError) as e:
                print(f"Aviso: Não foi possível carregar a fonte '{path}'. Usando a fonte padrão. Erro: {e}")
        return ImageFont.load_default()

    def add_component(self, name, x_position, flip=False, component_id=None, label_position='above'):
        """
        Adiciona um componente à lista para ser desenhado em uma posição X específica.

        Args:
            name (str): O caminho do arquivo do componente (shape).
            x_position (int): A coordenada X horizontal onde o componente será colocado.
            flip (bool, optional): Se True, a imagem será espelhada horizontalmente.
            component_id (int, optional): O ID numérico do componente. Se None,
                                          será atribuído um ID sequencial.
            label_position (str, optional): A posição da etiqueta de numeração.
                                            Pode ser 'above' (padrão) ou 'below'.
        """
        self._check_file_exists(name)
        self.components_to_draw.append({
            "name": name,
            "x_position": x_position,
            "flip": flip,
            "id": component_id if component_id is not None else len(self.components_to_draw) + 1,
            "label_position": label_position
        })

    def _draw_component_label_with_arrow(self, component_bbox, component_id,
                                         label_position='above', 
                                         arrow_color="black", arrow_width=6):
        
        comp_x_center = (component_bbox[0] + component_bbox[2]) // 2
        comp_y_center = (component_bbox[1] + component_bbox[3]) // 2
        
        text_to_draw = str(component_id)
        text_bbox = self.font.getbbox(text_to_draw)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        if label_position == 'below':
            # Definindo a nova posição horizontal para o número e a seta quando ao lado direito
            label_x = comp_x_center

            label_offset_y = 300  
            arrow_start_y = comp_y_center + 160
            arrow_end_y = comp_y_center + label_offset_y - 60
            text_y = comp_y_center + label_offset_y + 10

            arrowhead = [
                (label_x - 10, arrow_start_y),
                (label_x + 10, arrow_start_y),
                (label_x, arrow_start_y - 10)
            ]
            self.draw.line([(label_x, arrow_start_y), (label_x, arrow_end_y)],
                           fill=arrow_color, width=arrow_width)
            self.draw.polygon(arrowhead, fill=arrow_color)
            self.draw.text((label_x - (text_width // 2), text_y), text_to_draw, fill=arrow_color, font=self.font)

        else: # 'above'
            # Definindo a nova posição horizontal para o número e a seta quando ao lado esquerdo
            label_x = comp_x_center

            label_offset_y = -300
            arrow_start_y = comp_y_center - 160
            arrow_end_y = comp_y_center + label_offset_y + 60
            text_y = comp_y_center + label_offset_y - 10
            
            arrowhead = [
                (label_x - 10, arrow_start_y),
                (label_x + 10, arrow_start_y),
                (label_x, arrow_start_y + 10)
            ]
            self.draw.line([(label_x, arrow_start_y), (label_x, arrow_end_y)],
                           fill=arrow_color, width=arrow_width)
            self.draw.polygon(arrowhead, fill=arrow_color)
            self.draw.text((label_x - (text_width // 2), text_y), text_to_draw, fill=arrow_color, font=self.font)
        
    def assemble_duct(self, component_y_offset=0):
        """
        Monta o duto sobrepondo todos os componentes na ordem em que foram adicionados.
        """
        for info in self.components_to_draw:
            component_image = Image.open(info["name"]).convert('RGBA')
            original_x_position = info["x_position"]
            x_position = original_x_position
            
            if info.get("flip", False):
                component_image = component_image.transpose(Image.FLIP_LEFT_RIGHT)
                x_position = self.background.width - (original_x_position + component_image.width)
            
            comp_width, comp_height = component_image.size
            y_position = (self.background.height - comp_height) // 2 + component_y_offset
            component_bbox = (x_position, y_position, x_position + comp_width, y_position + comp_height)

            self.background.alpha_composite(component_image, (x_position, y_position))
            self._draw_component_label_with_arrow(component_bbox, info["id"], info["label_position"])

        return self.background

def main():

    """
    Lógica principal para executar o script e gerar a imagem final.
    """
    pasta = "figuras"
    background_path = os.path.join(pasta, "duto.png")
    font_path = "arial.ttf"
    json_path = "input.json"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            df = pd.DataFrame(dados["Fittings"])
            print(df)

        
        composer = ImageComposer(background_path, font_path, font_size=60)
        
        x_positions_map = {  # Valores de x_position para cada tipo de acessório
                
            #       Tipo de linha: Flexivel            #
            #------------------------------------------#
            "Cabeça de Tração": 350,    #Pulling Head
            "Cabeça de Tração Perfilada": 000,
            "Conector": 450,    #End Fitting
            "Adaptador de Flanges": 350,    #Flange Adapter
            "Protetor de Flanges": 405, #Polymeric Clamp Protection
            "Vértebra": 000,    #Restrictor
            "Uraduct / Capa de linha": 000, #Uraduct
            "Enrijecedor intermediário": 000,   #Intermediate Stiffener
            "Enrijecedor de topo com capacete": 000,
            "Enrijecedor de topo sem capacete": 000,    #Top Stiffener
            "Kit de pull-in": 000,  #Pull-In Collar
            "Colar batente": 000,   #Stopper Collar	
            "Colar de peso morto": 000, #Dead Weight Collar
            "Flutuador de lazy wave": 000,  #Buoys for Lazy Wave
            "Colar de Anodo (conector)": 550,   #Set of Anode Collar
            "Colar de Anodo (linha)": 000,  #
            "Colar de Ancoragem": 600,  #Anchorage Collar
            
            #       Tipo de linha: Umbilical           #
            #------------------------------------------#
            "Cabeça de Tração Fina": 000,   #
            "Conector de Tração Bojuda": 000,   #
            "Armour pot sem olhal": 450,    #Armour Pot
            "Armour por com olhal": 000,    #
            "Caixa de emenda": 000,         #Junction Box
        }

        for section_id in set(df.IdPipeSection.to_list()):
            FilterPipe = df[df.IdPipeSection == section_id]
            for End in FilterPipe.Location.to_list():
                fittings = FilterPipe[FilterPipe.Location == End]
                
                for i, linha in enumerate(fittings.to_dict("records")):
                    tipo = linha["AccessoryType"]
                    nome_arquivo = f"{tipo}.png"
                    caminho_imagem = os.path.join(pasta, nome_arquivo)

                    flip = linha["Location"] == "EndB"     # Inverte se estiver no EndA
                    component_id = linha["IdPipeSection"]
                    label_position = 'below' if flip else 'above'

                    x_position = x_positions_map.get(tipo, 350)  # valor padrão caso não esteja no dicionário

                    #numero_sequencial = 

                    composer.add_component(
                            caminho_imagem,
                            x_position=x_position,
                            flip=flip,
                            component_id=numero_sequencial,
                            label_position=label_position
                    )   



    # try:
    #     composer = ImageComposer(background_path, font_path, font_size=60)
    #     """
    #     Valor de x_position ajustado para alinhar corretamente os componentes no duto.
    #     - Conector: 450
    #     - Adaptador de Flanges: 350
    #     - Protetor de Flanges: 405
    #     - Colar de Ancoragem: 600
    #     - Cabeça de Tração: 350
    #     - Colar de Anodo (conector): 550
    #     """
    #     # Componentes a serem adicionados
    #     composer.add_component(os.path.join(pasta, "adaptador_de_flanges.png"), x_position=350, component_id=1)
    #     composer.add_component(os.path.join(pasta, "conector.png"), x_position=450, component_id=2, label_position='below')
    #     composer.add_component(os.path.join(pasta, "protetor_de_flanges.png"), x_position=405, component_id=3)
    #     composer.add_component(os.path.join(pasta, "colar_de_ancoragem.png"), x_position=600, component_id=4)
    #     composer.add_component(os.path.join(pasta, "cabeca_de_tracao.png"), x_position=350, flip=True, component_id=6)
    #     composer.add_component(os.path.join(pasta, "conector.png"), x_position=450, flip=True, component_id=7) 
    #     composer.add_component(os.path.join(pasta, "colar_de_anodo(conector).png"), x_position=550, component_id=8)
        
        final_image = composer.assemble_duct(component_y_offset=0)
        final_image.show()
        #final_image.save("duto_montado.png")

    except FileNotFoundError as e:
        print(f"Erro: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    main()