import torch
import os
from pathlib import Path

def merge_checkpoint_to_model(checkpoint_dir, model_path=None, output_path="final_model.pt"):
    """
    Merge checkpoints from a directory into a final model and save it.
    
    Args:
        checkpoint_dir: Path to the directory containing checkpoint files
        model_path: Path to the base model file (optional, uses first checkpoint if not provided)
        output_path: Path to save the merged model
    """
    # Find all .pt files in checkpoint directory
    checkpoint_path = Path(checkpoint_dir)
    checkpoint_files = sorted(checkpoint_path.glob('*.pt'))
    
    if not checkpoint_files:
        print(f"No checkpoint files found in {checkpoint_dir}")
        return
    
    print(f"Found {len(checkpoint_files)} checkpoint(s)")
    
    # Load base model or use first checkpoint as base
    if model_path and os.path.exists(model_path):
        print(f"Loading base model from {model_path}")
        model_state = torch.load(model_path, map_location='cpu')
        checkpoints_to_merge = checkpoint_files
    else:
        print(f"No base model provided, using first checkpoint as base")
        model_state = torch.load(checkpoint_files[0], map_location='cpu')
        checkpoints_to_merge = checkpoint_files[1:]
    
    # Find all .pt files in checkpoint directory
    checkpoint_path = Path(checkpoint_dir)
    checkpoint_files = sorted(checkpoint_path.glob('*.pt'))
    
    if not checkpoint_files:
        print(f"No checkpoint files found in {checkpoint_dir}")
        return
    
    print(f"Found {len(checkpoint_files)} checkpoint(s)")
    
    # Load base model or use first checkpoint as base
    if model_path and os.path.exists(model_path):
        print(f"Loading base model from {model_path}")
        model_state = torch.load(model_path, map_location='cpu')
        checkpoints_to_merge = checkpoint_files
    else:
        print(f"No base model provided, using first checkpoint as base")
        model_state = torch.load(checkpoint_files[0], map_location='cpu')
        checkpoints_to_merge = checkpoint_files[1:]
    
    # Merge each checkpoint into the model
    for checkpoint_file in checkpoints_to_merge:
        print(f"Merging {checkpoint_file.name}...")
        checkpoint = torch.load(checkpoint_file, map_location='cpu')
        
        # Extract state_dict if checkpoint contains additional metadata
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            checkpoint_state = checkpoint['model_state_dict']
        else:
            checkpoint_state = checkpoint
        
        # Update model with checkpoint weights
        model_state.update(checkpoint_state)
    
    # Save merged model
    torch.save(model_state, output_path)
    print(f"Merged model saved to {output_path}")

if __name__ == "__main__":
    checkpoint_dir = "./checkpoints"
    model_path = None  # Leave as None if you only have checkpoints
    output_path = "TinyGEORGE.pt"
    
    merge_checkpoint_to_model(checkpoint_dir, model_path, output_path)