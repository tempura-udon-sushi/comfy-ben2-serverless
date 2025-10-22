"""
Memory Management Nodes for ComfyUI
Clean VRAM and free memory - MIT License compatible
"""

import gc
import torch
import comfy.model_management as mm


class FreeVRAM:
    """
    Free VRAM by clearing caches and running garbage collection
    Useful between heavy operations or when switching models
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "mode": (["soft", "aggressive"], {"default": "soft"}),
                "unload_models": ("BOOLEAN", {"default": False, "tooltip": "Unload all models from VRAM"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "free_vram"
    CATEGORY = "utils"
    OUTPUT_NODE = True
    
    def free_vram(self, mode="soft", unload_models=False, **kwargs):
        """
        Free VRAM and clear caches
        
        Args:
            mode: 'soft' for normal clearing, 'aggressive' for deep cleaning
            unload_models: If True, unload all models from VRAM
            **kwargs: Backward compatibility for old workflows
        """
        
        if mode == "aggressive":
            # Aggressive mode: Run garbage collection first
            print("🧹 Aggressive VRAM cleanup...")
            gc.collect()
            gc.collect()  # Run twice for better cleanup
        
        if unload_models:
            # Unload all models from VRAM
            print("📤 Unloading all models from VRAM...")
            mm.unload_all_models()
        
        # Clear device caches
        print("🗑️ Clearing device caches...")
        mm.soft_empty_cache()
        
        if mode == "aggressive":
            # Run garbage collection again after clearing caches
            gc.collect()
        
        # Get memory stats
        if torch.cuda.is_available():
            device = mm.get_torch_device()
            try:
                allocated = torch.cuda.memory_allocated(device) / (1024**3)
                reserved = torch.cuda.memory_reserved(device) / (1024**3)
                print(f"✅ VRAM cleared - Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")
            except:
                print("✅ VRAM cleared")
        else:
            print("✅ Memory cleared (CPU mode)")
        
        return {}


class VRAMMonitor:
    """
    Monitor VRAM usage and display statistics
    Does not modify anything, just reports
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "show_details": ("BOOLEAN", {"default": True}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("vram_info",)
    FUNCTION = "monitor_vram"
    CATEGORY = "utils"
    OUTPUT_NODE = True
    
    def monitor_vram(self, show_details=True, **kwargs):
        """
        Monitor and report VRAM usage
        
        Args:
            show_details: Show detailed information
            **kwargs: Backward compatibility for old workflows
        
        Returns:
            vram_info: String with VRAM information
        """
        
        vram_info = []
        
        if torch.cuda.is_available():
            device = mm.get_torch_device()
            
            try:
                # Get VRAM statistics
                allocated = torch.cuda.memory_allocated(device) / (1024**3)
                reserved = torch.cuda.memory_reserved(device) / (1024**3)
                total = torch.cuda.get_device_properties(device).total_memory / (1024**3)
                free = total - reserved
                
                vram_info.append(f"🎮 VRAM Status:")
                vram_info.append(f"  Allocated: {allocated:.2f} GB")
                vram_info.append(f"  Reserved:  {reserved:.2f} GB")
                vram_info.append(f"  Free:      {free:.2f} GB")
                vram_info.append(f"  Total:     {total:.2f} GB")
                vram_info.append(f"  Usage:     {(reserved/total*100):.1f}%")
                
                if show_details:
                    # Get free memory from ComfyUI's perspective
                    try:
                        free_mem = mm.get_free_memory(device) / (1024**3)
                        vram_info.append(f"  Available for models: {free_mem:.2f} GB")
                    except:
                        pass
                
                info_str = "\n".join(vram_info)
                print(info_str)
                
            except Exception as e:
                info_str = f"⚠️ Could not get VRAM info: {str(e)}"
                print(info_str)
                vram_info.append(info_str)
        else:
            info_str = "💻 Running in CPU mode (no VRAM)"
            print(info_str)
            vram_info.append(info_str)
        
        return ("\n".join(vram_info),)


class FreeVRAMAutomatic:
    """
    Automatically free VRAM when executed
    Useful to place in workflow to periodically clear memory
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "trigger": ("BOOLEAN", {"default": True, "tooltip": "Enable automatic VRAM clearing"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "auto_free_vram"
    CATEGORY = "utils"
    OUTPUT_NODE = True
    
    def auto_free_vram(self, trigger=True, **kwargs):
        """
        Automatically free VRAM when executed
        
        Args:
            trigger: Enable automatic VRAM clearing
            **kwargs: Backward compatibility for old workflows
        """
        
        if trigger:
            print("🔄 Auto-clearing VRAM...")
            gc.collect()
            mm.soft_empty_cache()
            
            if torch.cuda.is_available():
                device = mm.get_torch_device()
                try:
                    allocated = torch.cuda.memory_allocated(device) / (1024**3)
                    print(f"✅ Auto-clear complete - Allocated: {allocated:.2f}GB")
                except:
                    print("✅ Auto-clear complete")
        
        return {}


class FreeVRAMInline:
    """
    Free VRAM inline - can be placed between nodes in workflow
    Passes image through while clearing VRAM
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "mode": (["soft", "aggressive"], {"default": "soft"}),
                "unload_models": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "free_vram_inline"
    CATEGORY = "utils"
    
    def free_vram_inline(self, image, mode="soft", unload_models=False):
        """Free VRAM and pass image through"""
        
        if mode == "aggressive":
            print("🧹 Aggressive VRAM cleanup (inline)...")
            gc.collect()
            gc.collect()
        
        if unload_models:
            print("📤 Unloading all models from VRAM (inline)...")
            mm.unload_all_models()
        
        print("🗑️ Clearing device caches (inline)...")
        mm.soft_empty_cache()
        
        if mode == "aggressive":
            gc.collect()
        
        if torch.cuda.is_available():
            device = mm.get_torch_device()
            try:
                allocated = torch.cuda.memory_allocated(device) / (1024**3)
                reserved = torch.cuda.memory_reserved(device) / (1024**3)
                print(f"✅ VRAM cleared (inline) - Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")
            except:
                print("✅ VRAM cleared (inline)")
        else:
            print("✅ Memory cleared (inline, CPU mode)")
        
        return (image,)


class VRAMMonitorInline:
    """
    Monitor VRAM inline - can be placed between nodes
    Passes image through and reports VRAM stats
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "show_details": ("BOOLEAN", {"default": True}),
                "prefix": ("STRING", {"default": "", "tooltip": "Label to identify this checkpoint"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "vram_info")
    FUNCTION = "monitor_vram_inline"
    CATEGORY = "utils"
    
    def monitor_vram_inline(self, image, show_details=True, prefix=""):
        """Monitor VRAM and pass image through"""
        
        vram_info = []
        label = f"[{prefix}] " if prefix else ""
        
        if torch.cuda.is_available():
            device = mm.get_torch_device()
            
            try:
                allocated = torch.cuda.memory_allocated(device) / (1024**3)
                reserved = torch.cuda.memory_reserved(device) / (1024**3)
                total = torch.cuda.get_device_properties(device).total_memory / (1024**3)
                free = total - reserved
                
                vram_info.append(f"🎮 {label}VRAM Status:")
                vram_info.append(f"  Allocated: {allocated:.2f} GB")
                vram_info.append(f"  Reserved:  {reserved:.2f} GB")
                vram_info.append(f"  Free:      {free:.2f} GB")
                vram_info.append(f"  Total:     {total:.2f} GB")
                vram_info.append(f"  Usage:     {(reserved/total*100):.1f}%")
                
                if show_details:
                    try:
                        free_mem = mm.get_free_memory(device) / (1024**3)
                        vram_info.append(f"  Available for models: {free_mem:.2f} GB")
                    except:
                        pass
                
                info_str = "\n".join(vram_info)
                print(info_str)
                
            except Exception as e:
                info_str = f"⚠️ {label}Could not get VRAM info: {str(e)}"
                print(info_str)
                vram_info.append(info_str)
        else:
            info_str = f"💻 {label}Running in CPU mode (no VRAM)"
            print(info_str)
            vram_info.append(info_str)
        
        return (image, "\n".join(vram_info))


NODE_CLASS_MAPPINGS = {
    "FreeVRAM": FreeVRAM,
    "VRAMMonitor": VRAMMonitor,
    "FreeVRAMAutomatic": FreeVRAMAutomatic,
    "FreeVRAMInline": FreeVRAMInline,
    "VRAMMonitorInline": VRAMMonitorInline,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FreeVRAM": "Free VRAM (Standalone)",
    "VRAMMonitor": "VRAM Monitor (Standalone)",
    "FreeVRAMAutomatic": "Free VRAM (Auto)",
    "FreeVRAMInline": "Free VRAM (Inline)",
    "VRAMMonitorInline": "VRAM Monitor (Inline)",
}
