from PIL import Image, ImageDraw, ImageFont
import os
import json
import pandas as pd

"""
Classe para compor uma imagem de fundo com múltiplos componentes (shapes) e adicionar numeração com setas.
"""
class ImageComposer:

    #  INICIALIZAÇÃO
    def __init__(self, background_path, font_path=None, font_size=60):
        """
        Inicializa a classe com o caminho da imagem de fundo e a fonte para numeração.
        """
        self._check_file_exists(background_path)
        self.background = Image.open(background_path).convert('RGBA')
        self.draw = ImageDraw.Draw(self.background)
        self.components_to_draw = []
        self.font = self._load_font(font_path, font_size)
 
    #  VERIFICAÇÃO DE ARQUIVO
    def _check_file_exists(self, path):
        # Verifica se um arquivo existe, levantando uma exceção se não.
        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo '{path}' não encontrado!")
 
    #  CARREGA A FONTE
    def _load_font(self, path, size):
        # Tenta carregar a fonte especificada, caso contrário, usa a padrão.
        if path:
            try:
                return ImageFont.truetype(path, size)
            except (IOError, OSError) as e:
                print(f"Aviso: Não foi possível carregar a fonte '{path}'. Usando a fonte padrão. Erro: {e}")
        return ImageFont.load_default()
    
        # NOVO: Função para ajustar a posição X
    def _adjust_x_position(self, fittings_list, current_fitting):
        """
        Ajusta a posição X de um componente com base nos outros componentes
        presentes na mesma seção.
        """
        x_position = current_fitting.get("x_position", 0)
        tipos_acessorios = {f['AccessoryType'] for f in fittings_list}
        current_type = current_fitting.get("AccessoryType")
        
        # Exemplo: Se há um "Flange Adapter" e o componente atual é uma "Pulling Head"
        if "Flange Adapter" in tipos_acessorios and "Pulling Head" in current_type:
            # Aumenta o valor de X em 200, mas apenas para o lado 'EndB' (direita)
            if current_fitting.get("Location") == "EndA":
                return x_position - 100

        # Você pode adicionar mais regras aqui conforme a necessidade
        # Exemplo: Se há um "Armour Pot" e o componente é um "Junction Box", ajusta Y
        # if "Armour Pot(w eyelet)" in tipos_acessorios and "Junction Box" in current_type:
        #     current_fitting['y_position'] = 50 # Exemplo de ajuste de Y, se necessário

        return x_position




    #  REGRAS DE POSICIONAMENTO DA ETIQUETA
    def _should_label_be_below(self, fittings_list, current_fitting_type):
        """
        Determina se a etiqueta de numeração deve ser 'below'.
 
        Você pode customizar essa função com qualquer regra. Por exemplo:
        se o componente atual for um 'Colar' e a seção também contém um 'Conector'.
        """
        tipos_acessorios = [f['AccessoryType'] for f in fittings_list]
        
        # Regra de exemplo: Se o componente atual é um 'Colar de Anodo' e
        # na mesma seção existe um 'Conector', a etiqueta deve ficar 'below'.
        
        rules = [
                ("Set of Anode Collar" in current_fitting_type and "End Fitting" in tipos_acessorios),
                ("Pull-In Collar" in current_fitting_type and "End Fitting" in tipos_acessorios),
                ("Flange Protector" in current_fitting_type and "End Fitting" in tipos_acessorios),
            ]
        # Exemplo: Se for um "Flutuador" e a seção tiver mais de 3 componentes
        # is_special_case = ("Flutuador" in current_fitting_type and len(fittings_list) > 3)
 
        return any(rules)
    
    #   ADICIONA COMPONENTES
    def add_component(self, name, x_position, flip=False, component_id=None, label_position='above'):
        """
        Adiciona um componente à lista para ser desenhado em uma posição X específica.
        Args:
            name (str): O caminho do arquivo do componente (shape).
            x_position (int): A coordenada X horizontal onde o componente será colocado.
            flip (bool, optional): Se True, a imagem será espelhada horizontalmente.
            component_id (int, optional): O ID numérico do componente. Se None, será atribuído um ID sequencial.
            label_position (str, optional): A posição da etiqueta de numeração. Pode ser 'above' (padrão) ou 'below'.
        """
        self._check_file_exists(name)
        self.components_to_draw.append({
            "name": name,
            "x_position": x_position,
            "flip": flip,
            "id": component_id if component_id is not None else len(self.components_to_draw) + 1,
            "label_position": label_position
        })

    #   CONTRUÇÃO DA SETA E NÚMERO
    def _draw_component_label_with_arrow(self, component_bbox, component_id, 
                                         label_position='above', arrow_color="black", 
                                         arrow_width=6):
        comp_x_center = (component_bbox[0] + component_bbox[2]) // 2
        comp_y_center = (component_bbox[1] + component_bbox[3]) // 2
        text_to_draw = str(component_id)
        text_bbox = self.font.getbbox(text_to_draw)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Lógica de posicionamento para o número e a seta.

        if label_position == 'below': # EM BAIXO
            # Posiciona a seta e o texto abaixo do componente
            arrow_start_y = comp_y_center + 140 # Um pequeno offset abaixo do centro do componente
            arrow_end_y = comp_y_center + 230 # Posição final da seta
            text_y = arrow_end_y + 25 # Posição do texto abaixo da seta
 
            # Desenha a linha da seta
            self.draw.line([(comp_x_center, arrow_start_y), (comp_x_center, arrow_end_y)],
                           fill=arrow_color, width=arrow_width)
            
            # Desenha a ponta da seta (apontando para baixo)
            arrowhead = [
                (comp_x_center - 10, arrow_start_y),
                (comp_x_center + 10, arrow_start_y),
                (comp_x_center, arrow_start_y - 10)
            ]
            self.draw.polygon(arrowhead, fill=arrow_color)
            
            # Desenha o texto (o número do anel)
            self.draw.text((comp_x_center - (text_width // 2), text_y),
                           text_to_draw, fill=arrow_color, font=self.font)
 
        else: # 'above' EM CIMA
            # Posiciona a seta e o texto acima do componente
            arrow_start_y = comp_y_center - 160 # Um pequeno offset acima do centro do componente
            arrow_end_y = comp_y_center - 240 # Posição final da seta
            text_y = arrow_end_y - text_height - 25 # Posição do texto acima da seta
 
            # Desenha a linha da seta
            self.draw.line([(comp_x_center, arrow_start_y), (comp_x_center, arrow_end_y)],
                           fill=arrow_color, width=arrow_width)
            
            # Desenha a ponta da seta (apontando para cima)
            arrowhead = [
                (comp_x_center - 10, arrow_start_y),
                (comp_x_center + 10, arrow_start_y),
                (comp_x_center, arrow_start_y + 10)
            ]
            self.draw.polygon(arrowhead, fill=arrow_color)
 
            # Desenha o texto
            self.draw.text((comp_x_center - (text_width // 2), text_y),
                           text_to_draw, fill=arrow_color, font=self.font)
    
    #   MONTA O DUTO
    def assemble_duct(self, component_y_offset=0):
        """
        Monta o duto sobrepondo todos os componentes na ordem em que foram adicionados.
        """
        self.components_to_draw.sort(key=lambda item: item['x_position'])

        for i, info in enumerate(self.components_to_draw):
            info["id"] = i + 1

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
 
#   LÓGICA PRINCIPAL 
def main():
    """ Lógica principal para executar o script e gerar a imagem final. """
    pasta = "figuras"
    background_path = os.path.join(pasta, "Pipe.png")
    font_path = "arial.ttf"
    json_path = "input.json"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        df = pd.DataFrame(dados["Fittings"])
        #print(df)
 
        
        x_positions_map = {
            #       Tipo de linha: Flexivel            #
            #------------------------------------------#
            "Pulling Head": 330,    # Cabeça de Tração
            "Streamlined Pulling Head": 330, # Cabeça de Tração Perfilada
            "End Fitting": 430,    # Conector
            "Flange Adapter": 330,    # Adaptador de Flanges
            "Polymeric Clamp Protection": 380, # Protetor de Flanges
            "Restrictor": 662,    # Vértebra
            "Uraduct": 662, # Uraduct / Capa de linha
            "Intermediate Stiffener": 662,   # Enrijecedor intermediário
            "Top Stiffener(w helmet)": 640,   # Enrijecedor de topo com capacete
            "Top Stiffener(wo helmet)": 662,    # Enrijecedor de topo sem capacete
            "Pull-In Collar": 580,  # Kit de pull-in
            "Stopper Collar": 1015,  # Colar batente
            "Dead Weight Collar": 550, # Colar de peso morto
            "Buoys for Lazy Wave": 1127,  # Flutuador de lazy wave
            "Set of Anode Collar(end fitting)": 530,   # Colar de Anodo (conector)
            "Set of Anode Collar(line)": 710,  # Colar de Anodo (linha) / se tiver componente maiores (930)
            "Set of Anode Collar": 710,
            "Anchorage Collar": 580,  # Colar de Ancoragem
            "Anchorage Collar(inverted):": 580,  # Colar de Ancoragem Invertido
            #       Tipo de linha: Umbilical           #
            #------------------------------------------#
            "Slim Pulling Head": 000,   # Cabeça de Tração Fina
            "Anchorage Collar2": 580,  # Colar de Ancoragem Umbilical
            "Anchorage Collar2(inverted)": 580,  # Colar de Ancoragem Umbilical
            "Buldous Pulling Connector": 000,   # Conector de Tração Bojuda
            "Armour Pot(w eyelet)": 430,    # Armour por com olhal
            "Armour Pot(wo eyelet)": 430,    # Armour pot sem olhal
            "Junction Box": 000,         #Caixa de Emenda
        }
 
        for section_id in sorted(df.IdPipeSection.unique()):
            composer = ImageComposer(background_path, font_path, font_size=60)
            filter_pipe = df[df.IdPipeSection == section_id]
            fittings_in_section = filter_pipe.to_dict("records")

            for i, linha in enumerate(fittings_in_section):
                tipo = linha["AccessoryType"]
                nome_arquivo = f"{tipo}.png"
                path_imagem = os.path.join(pasta, nome_arquivo)
                
                if os.path.exists(path_imagem):
                    flip = linha["Location"] == "EndA"
                    component_id = i + 1
                    
                    # 1. Obter a posição X inicial do mapa
                    initial_x_position = x_positions_map.get(tipo, 0)
                    
                    # 2. Criar um dicionário temporário para passar à função
                    # Adiciona a posição inicial e o tipo ao dicionário da linha
                    linha["x_position"] = initial_x_position
                    
                    # 3. Chamar a nova função para ajustar a posição X
                    x_position_ajustada = composer._adjust_x_position(fittings_in_section, linha)

                    if composer._should_label_be_below(fittings_in_section, tipo):
                        label_position = 'below'
                    else:
                        label_position = 'above'

                    composer.add_component(
                        path_imagem,
                        x_position=x_position_ajustada, # Usar a nova posição ajustada aqui
                        flip=flip,
                        component_id=component_id,
                        label_position=label_position
                    )
                else:
                    print(f"Aviso Sobre o ID {section_id}: Imagem '{path_imagem}' para o componente '{tipo}' não encontrada.")

            final_image = composer.assemble_duct(component_y_offset=0)
            output_filename = f"Pipe_Finished_ID_{section_id}.png"
            final_image.save(output_filename)
            print(f"Imagem gerada e salva como '{output_filename}'")
            #final_image.show()

    except FileNotFoundError as e:
        print(f"Erro: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    main()