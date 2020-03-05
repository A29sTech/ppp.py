from PIL import Image, ImageOps
from typing import Union, List, Tuple



#---------------------------- Util Fuctions ----------------------------#
def mm2px(mm):
    return int((mm/25.4 )*300)



#------------------------- Paper & Layer CLASS -------------------------#
class Layer():
    def __init__(self, layer: Image, name: str = "layer"):
        self.img = layer
        self.name = name
        self.__orginal: Union[Image, None] = None

    def commit(self):
        """ Save Orgianl Layer From Changes """
        self.__orginal = self.img
        return self

    def undo(self):
        """ Undo To Commit """
        if self.__orginal:
            self.img = self.__orginal
            self.__orginal = None
        return self

    def resize(self, width: int, height: int = 0):

        # Getiing Orginal Layer Size#
        w = self.img.size[0]
        h = self.img.size[1]

        # Get Ration If One Of Arg Is Less Then 1px #
        if ( width < 1 and height > 1 ):
            ratio = w / h
            w = int(height * ratio)
            h = height
        elif ( width > 1 and height < 1  ):
            ratio = h / w
            w = width
            h = int(width * ratio)
        else:
            w = width
            h = height

        # Do Main Oparation #
        self.img = self.img.resize( (w, h), Image.LANCZOS)
        return self

    def border(self, size: int, color: str = "black"):
        self.img = ImageOps.expand(self.img, border = size, fill = color ) # PX Border.
        return self

class Paper():
    class _Layer_Container():
        def __init__(self, layer: Layer, noc: int):
            self.noc = noc
            self.layer = layer

    def __init__(self, width: int, height: int, color: str = 'white'):
        self.__width = width
        self.__height = height
        self.__color = color
        self.__border =  0
        self.__layers: List[self._Layer_Container] = []
        self.__overflow = []

    @property
    def width(self) -> int:
        return self.width

    @property
    def height(self) -> int:
        return self.__height

    @property
    def info(self) -> Tuple[int, int, int, str]:
        return (self.__width, self.__height, self.__border, self.__color)

    def resize(self, width: int, height: int):
        self.__width = width
        self.__height = height

    def set_border(self, border_px:int):
        self.__border = border_px

    def set_color(self, color: str):
        self.__color = color

    def add(self, layer: Layer, noc = 1) -> None:
        self.__layers.append(self._Layer_Container( layer, noc ))

    def remove(self, name: str) -> Union[Layer, None]:
        for layerc in self.__layers:
            if layerc.layer.name == name:
                removed = layerc
                self.__layers.remove(layerc)
                return removed
                
        return None
        
    def get_layers_name(self) -> List[str]:
        names: List[str] = []
        for layerc in self.__layers:
            names.append(layerc.layer.name)
        return names

    def clear(self) -> None:
        """ Remove All Layer From Paper """
        self.__layers = []
        self.__overflow = []

    class _Cursor():
        def __init__(self, x: int, y: int, w: int, h: int):
                self.__x = x
                self.__y = y
                self.__w = w
                self.__h = h
                # Current Cursor Tracker.
                self._cx = x
                self._cy = y
                self._direction = 'R'
                self.__overflow = 0
                
                self.__spacing = 0

        @property
        def is_overflow(self) -> int:
            return self.__overflow

        def go_right(self) -> Tuple[int, int]:
            self.__overflow = 0
            self._cx = self.__x
            self._cy = self.__y
            self._direction = 'R'
            return (self._cx, self._cy)

        def go_left(self):
            self.__overflow = 0
            self._cx = self.__x + self.__w
            self._cy = self.__y
            self._direction = 'L'
            return (self._cx, self._cy)

        def next(self, w: int, h: int) -> bool:
            # Right Logic #
            if ( self._direction == 'R' ):
                # Hold State
                xPos, yPos = (self._cx, self._cy)
                # Chack For Right
                if ((self._cx + w) < (self.__x + self.__w)):
                    """ Go Right """
                    self._cx = self._cx + w + self.__spacing
                    return ( xPos, yPos )

                # CHeck For Next Line
                elif ((self._cy + h) < (self.__y + self.__h)):
                    """ Go To Next Line """
                    self._cx = xPos = self.__x
                    self._cy = self._cy + h + self.__spacing
                    return self.next( w, h ) # Expromentel

                else:
                    """ Stay In Place """
                    self.__overflow += 1



            # Left Logic #
            elif ( self._direction == 'L' ):
                # Check Left
                if ( (self._cx - w) > self.__x ):
                    """ Go Left """
                    self._cx = self._cx - w - self.__spacing
                    return ( self._cx, self._cy )

                # Check For Next Line
                elif ((self._cy + h) < (self.__y + self.__h)):
                        """ Go To Next Line """
                        self._cx = (self.__x + self.__w)
                        self._cy = self._cy + h + self.__spacing
                        return self.next( w, h ) # Expromentel
                        #return ( self._cx, self._cy )

                else:
                    """ Stay In Place """
                    self.__overflow += 1

            return (self._cx, self._cy)

        def set_spacing(self, spacing: int):
            self.__spacing = spacing
            
    def _validate_render_arg(self, width, height):
        # Check Args.
        if ( width < 1 and height > 1 ):
            width = self.__width - (self.__border + self.__border)
        elif ( width > 1 and height < 1 ):
            height = self.__height - (self.__border + self.__border)
        elif ( width > 1 and height > 1 ):
            width = self.__width
            height = self.__height
        else:
            width = self.__width - (self.__border + self.__border)
            height = self.__height - (self.__border + self.__border)
            
        return ( width, height )

    def render(self, spacing: int, width=0, height=0, axis = 'R'):
        # Assign Arg To Local Variable
        w, h = self._validate_render_arg(width, height)
        # Create A PIL Image As Paper
        paper = Image.new('RGB', (self.__width, self.__height), color = self.__color)
        # Configure Cursor
        cursor = self._Cursor( self.__border, self.__border, w, h )
        
        # Set Spacing Betwen Layers
        cursor.set_spacing(spacing)

        # Set Axis 
        if ( axis == 'R' ):
            cursor.go_right()
        elif ( axis == 'L' ):
            cursor.go_left()
        # Loop & Place All Layer.
        for layerc in self.__layers:
            # noc means Number Of Copy
            for _ in range(layerc.noc):
                # Get Layer Size.
                layer_width, layer_height = layerc.layer.img.size
                _w, _h = cursor.next(layer_width, layer_height)
                if cursor.is_overflow:
                    self.__overflow.append(layerc)
                else:
                    paper.paste(layerc.layer.img, ( _w, _h ))

        return paper

    def load_overflow(self) -> int:
        overflow_count = len(self.__overflow)
        if ( overflow_count > 0 ):
            self.__layers = self.__overflow
            return overflow_count
        else:
            return 0
        
    


# Testing...
if __name__ == '__main__':
    # Give 2 Image Path
    IMG_1 = 'xmp1.jpg'
    IMG_2 = 'xmp2.jpg'

    # Create A A4 Paper
    paper = Paper( mm2px(210), mm2px(297) )
    paper.set_border( mm2px( 2 ) )
    paper.set_color('red')
    # Create Some Layer
    layer1 = Layer( Image.open( IMG_1 ) ) 
    layer2 = Layer( Image.open( IMG_2 ) )
    layer1.resize( mm2px(27) )
    layer1.border( 3 ) # 3 Pixel Border
    layer2.resize( mm2px(28) )
    layer2.border( 3 ) # 3 Pixel Border

    paper.add( layer1, 5 )
    paper.add( layer2, 10 )
    paper.render(mm2px( 1 ), 0, 0, 'R').save('example_out.jpg')


